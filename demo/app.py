import os
import time
import threading
import datetime
from pathlib import Path

# Keep Ultralytics settings writable in restricted Windows and container environments.
CACHE_DIR = Path(__file__).resolve().parent / ".cache"
CACHE_DIR.mkdir(exist_ok=True)
os.environ.setdefault("YOLO_CONFIG_DIR", str(CACHE_DIR))
os.environ.setdefault("MPLCONFIGDIR", str(CACHE_DIR / "matplotlib"))

import cv2
import numpy as np
from flask import Flask, Response, jsonify, request, send_from_directory
from werkzeug.utils import secure_filename
from ultralytics import YOLO

app = Flask(__name__, static_folder='.', static_url_path='')

BASE_DIR = os.path.dirname(__file__)
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
ALLOWED_EXTENSIONS = {'mp4', 'mkv', 'avi', 'mov', 'webm'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500 MB max upload

# webapp/app.py -> ../model/best.pt
MODEL_PATH = Path(BASE_DIR).resolve() / "model" / "best.pt"
CONF_THRESHOLD = 0.35
INFER_IMG_SIZE = 256        # lower = faster, less accurate (try 256/320/416/640)
DETECT_INTERVAL_SEC = 1.5   # run YOLO at most once every this many seconds


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


class VideoProcessor:
    def __init__(self):
        self.video_path = None
        self.cap = None
        self.running = True

        if not MODEL_PATH.is_file():
            raise FileNotFoundError(
                f"YOLO model not found at {MODEL_PATH}. "
                "Copy best.pt into the model/ folder next to webapp/."
            )
        self.model = YOLO(str(MODEL_PATH))
        # data.yaml -> 0: cleaner, 1: person
        self.class_names = {int(k): v for k, v in self.model.names.items()}

        self.student_count = 0
        self.cleaner_count = 0
        self.current_people_count = 0  # students only, drives AC logic
        self.occupancy_level = "LOW"
        self.ac_state = "OFF"
        self.ac_temp = "--°C"
        self.ac_last_changed = "--"
        self.prev_ac_state = "OFF"
        self.prev_ac_temp = "--°C"

        self.is_webcam = False
        self.ac_start_time = None
        self.ac_total_run_seconds = 0.0
        self.avg_confidence = 0.0

        self.recent_counts = []
        self.latest_jpg = None

        self.last_detected_student_count = None
        self.student_count_stable_since = time.time()
        self.ac_stability_delay = 5.0  # seconds with no changes in student count

        self.frame_counter = 0
        self.last_boxes = []
        self.last_detect_time = 0.0
        self.frame_interval = 0.033  # default ~30fps pacing between reads
        self.display_width = 640    # resize frames before draw/encode to cut CPU load

        self.thread = threading.Thread(target=self._process_loop, daemon=True)
        self.thread.start()

    def set_video_source(self, source):
        if self.cap:
            try:
                self.cap.release()
            except Exception:
                pass
            self.cap = None

        is_webcam = False
        source_str = str(source).strip()
        if isinstance(source, int) or source_str.isdigit():
            cam_idx = int(source_str)
            cap = cv2.VideoCapture(cam_idx)
            is_webcam = True
            source_desc = f"Live Camera Stream (Webcam {cam_idx})"
        else:
            cap = cv2.VideoCapture(source)
            source_desc = os.path.basename(source)

        if not cap.isOpened():
            cap.release()
            raise ValueError(f"Could not open video source: {source_desc}")

        self.video_path = source
        self.is_webcam = is_webcam
        self.cap = cap
        fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.frame_interval = (1.0 / fps) if fps and fps > 1 else 0.033
        self.recent_counts = []
        self.last_boxes = []
        self.last_detect_time = 0.0
        self.student_count = 0
        self.cleaner_count = 0
        self.avg_confidence = 0.0
        self.last_detected_student_count = None
        self.student_count_stable_since = time.time()
        self.update_ac_logic(0)
        print(f"[VideoProcessor] Switched video source to: {source_desc} (fps={fps})")

    def detect_people(self, frame):
        """Run real YOLO inference and split detections by class."""
        results = self.model.predict(
            frame,
            conf=CONF_THRESHOLD,
            imgsz=INFER_IMG_SIZE,
            verbose=False,
        )
        result = results[0]

        students = 0
        cleaners = 0
        boxes_to_draw = []
        confidences = []

        if result.boxes is not None:
            for box in result.boxes:
                cls_id = int(box.cls[0])
                name = self.class_names.get(cls_id, f"class_{cls_id}")
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                conf = float(box.conf[0])

                if name == "person":
                    students += 1
                elif name == "cleaner":
                    cleaners += 1

                confidences.append(conf)
                boxes_to_draw.append((x1, y1, x2, y2, name, conf))

        # Smooth the student count over the last few frames to avoid flicker
        self.recent_counts.append(students)
        if len(self.recent_counts) > 6:
            self.recent_counts.pop(0)
        smoothed_students = int(round(sum(self.recent_counts) / len(self.recent_counts)))

        avg_conf = float(sum(confidences) / len(confidences)) if confidences else 0.0

        return boxes_to_draw, smoothed_students, cleaners, avg_conf

    def update_ac_logic(self, student_count):
        """AC decisions are based on student count only, not cleaners."""
        self.current_people_count = student_count

        if student_count <= 2:
            new_state = "OFF"
            new_temp = "--°C"
        elif student_count <= 9:
            new_state = "ON"
            new_temp = "24°C"
        else:
            new_state = "ON"
            new_temp = "20°C"

        if new_state != self.prev_ac_state or new_temp != self.prev_ac_temp:
            now_ts = time.time()
            if new_state == "ON" and self.prev_ac_state == "OFF":
                self.ac_start_time = now_ts
            elif new_state == "OFF" and self.prev_ac_state == "ON":
                if self.ac_start_time is not None:
                    self.ac_total_run_seconds += (now_ts - self.ac_start_time)
                self.ac_start_time = None

            self.ac_state = new_state
            self.ac_temp = new_temp
            self.ac_last_changed = datetime.datetime.now().strftime("%I:%M:%S %p")
            self.prev_ac_state = new_state
            self.prev_ac_temp = new_temp

    def get_ac_run_time(self):
        total_sec = self.ac_total_run_seconds
        if self.ac_state == "ON" and self.ac_start_time is not None:
            total_sec += (time.time() - self.ac_start_time)

        hours = int(total_sec // 3600)
        minutes = int((total_sec % 3600) // 60)
        seconds = int(total_sec % 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def _process_loop(self):
        while self.running:
            try:
                if not self.cap or not self.cap.isOpened():
                    standby = np.ones((480, 800, 3), dtype=np.uint8) * 20
                    cv2.putText(standby, "CAMERA STANDBY", (270, 210),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 215, 255), 2)
                    cv2.putText(standby, "Please click Live WebCam or Upload Video to start AI processing", (120, 260),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (148, 163, 184), 1)
                    _, buffer = cv2.imencode('.jpg', standby)
                    self.latest_jpg = buffer.tobytes()
                    time.sleep(0.2)
                    continue

                ret, frame = self.cap.read()
                if not ret:
                    if self.video_path and not self.is_webcam:
                        self.cap.release()
                        self.cap = cv2.VideoCapture(self.video_path)
                    time.sleep(0.03)
                    continue

                # Downscale before detect/draw/encode to cut CPU load
                h, w = frame.shape[:2]
                if w > self.display_width:
                    scale = self.display_width / w
                    frame = cv2.resize(frame, (self.display_width, int(h * scale)))

                self.frame_counter += 1
                now = time.time()
                if now - self.last_detect_time >= DETECT_INTERVAL_SEC:
                    boxes, students, cleaners, avg_conf = self.detect_people(frame)
                    self.last_boxes = boxes
                    self.last_detect_time = now

                    # Track student count changes to enforce 5-second stability before changing AC
                    if self.last_detected_student_count is None or students != self.last_detected_student_count:
                        self.last_detected_student_count = students
                        self.student_count_stable_since = now

                    self.student_count = students
                    self.cleaner_count = cleaners
                    self.current_people_count = students
                    self.avg_confidence = avg_conf
                else:
                    boxes = self.last_boxes

                # Update live occupancy level based on current detected student count
                if self.student_count <= 2:
                    self.occupancy_level = "LOW"
                elif self.student_count <= 9:
                    self.occupancy_level = "MEDIUM"
                else:
                    self.occupancy_level = "HIGH"

                # Change AC status only after 5 seconds with no changes in student count
                if now - self.student_count_stable_since >= self.ac_stability_delay:
                    if self.last_detected_student_count is not None:
                        self.update_ac_logic(self.last_detected_student_count)

                for (x1, y1, x2, y2, name, conf) in boxes:
                    color = (0, 255, 127) if name == "person" else (56, 189, 248)
                    label = "Student" if name == "person" else "Cleaner"
                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                    cv2.putText(frame, f"{label} {conf:.2f}", (x1, max(y1 - 8, 20)),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

                conf_text = f"{self.avg_confidence * 100:.1f}%" if self.avg_confidence > 0 else "N/A"
                banner_text = (
                    f"AI Detected: {self.student_count} Students, {self.cleaner_count} Cleaners | "
                    f"Conf: {conf_text} | Occupancy: {self.occupancy_level} | AC: {self.ac_state} ({self.ac_temp})"
                )
                cv2.rectangle(frame, (0, 0), (frame.shape[1], 40), (15, 23, 42), -1)
                cv2.putText(frame, banner_text, (15, 26),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.55, (34, 210, 241), 2)

                _, buffer = cv2.imencode('.jpg', frame)
                self.latest_jpg = buffer.tobytes()

            except Exception as e:
                print(f"[ProcessLoop Error] {e}", flush=True)

            time.sleep(self.frame_interval)

    def generate_frames(self):
        while self.running:
            if self.latest_jpg is not None:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + self.latest_jpg + b'\r\n')
            time.sleep(0.04)

    def get_status(self):
        if self.is_webcam:
            current_source = f"Live Camera Stream ({self.video_path})"
        elif self.video_path:
            current_source = os.path.basename(str(self.video_path))
        else:
            current_source = "No Video Uploaded (Click Live WebCam or Upload Video)"

        conf_pct = round(self.avg_confidence * 100, 1)
        return {
            "people_count": self.current_people_count,
            "student_count": self.student_count,
            "cleaner_count": self.cleaner_count,
            "occupancy_level": self.occupancy_level,
            "ac_state": self.ac_state,
            "ac_temp": self.ac_temp,
            "ac_last_changed": self.ac_last_changed,
            "ac_run_time": self.get_ac_run_time(),
            "avg_confidence": f"{conf_pct:.1f}%" if self.avg_confidence > 0 else "N/A",
            "confidence_val": conf_pct,
            "is_webcam": self.is_webcam,
            "current_video": current_source
        }


video_processor = VideoProcessor()


@app.route('/')
def index():
    if os.path.exists(os.path.join(BASE_DIR, 'smart_classroom.html')):
        return send_from_directory('.', 'smart_classroom.html')
    return ("<h1>Edge AI AC Monitor</h1>"
            "<p>Frontend template <code>smart_classroom.html</code> is missing.</p>", 500)


@app.route('/video_feed')
def video_feed():
    return Response(video_processor.generate_frames(),
                     mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/api/live_status')
def live_status():
    return jsonify(video_processor.get_status())


@app.route('/api/upload_video', methods=['POST'])
def upload_video():
    if 'video' not in request.files:
        return jsonify({"success": False, "error": "No video file provided"}), 400

    file = request.files['video']
    if file.filename == '':
        return jsonify({"success": False, "error": "No file selected"}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(save_path)

        try:
            video_processor.set_video_source(save_path)
        except ValueError as exc:
            return jsonify({"success": False, "error": str(exc)}), 400

        return jsonify({
            "success": True,
            "filename": filename,
            "message": "Video uploaded and live YOLO processing started!"
        })

    return jsonify({"success": False, "error": "Invalid file format. Allowed formats: mp4, mkv, avi, mov, webm"}), 400


@app.route('/api/start_camera', methods=['POST'])
def start_camera():
    req_data = request.get_json(silent=True) or {}
    camera_index = req_data.get('camera_index', 0)
    try:
        video_processor.set_video_source(camera_index)
        return jsonify({
            "success": True,
            "message": f"Connected to live camera feed (device {camera_index})!"
        })
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 400


if __name__ == '__main__':
    print(f"Loading YOLO model from: {MODEL_PATH}")
    print("Starting Edge AI AC Monitor Backend Server on http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
