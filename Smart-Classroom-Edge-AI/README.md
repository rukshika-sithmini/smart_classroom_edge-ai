# Smart Classroom Edge AI

An edge-ready YOLOv8 project that detects and counts people and cleaners in
classroom images, videos, webcams, and network streams.

## Project structure

```text
Smart-Classroom-Edge-AI/
├── model/
│   └── best.pt
├── training/
│   └── yolov8_training.ipynb
├── inference/
│   └── detect_and_count.py
├── data.yaml
├── requirements.txt
├── README.md
└── .gitignore
```

The trained model uses these classes:

- `0`: cleaner
- `1`: person (reported as a student)

## Setup

Python 3.9 or newer is recommended.

```bash
python -m venv .venv
```

Activate the environment:

```bash
# Windows
.venv\Scripts\activate

# Linux/macOS
source .venv/bin/activate
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

## Inference

Pass an image, video, directory, stream URL, or webcam index:

```bash
python inference/detect_and_count.py classroom_video.mp4
python inference/detect_and_count.py classroom.jpg --save
python inference/detect_and_count.py 0 --show
```

Useful options:

```text
--conf 0.35       detection confidence threshold
--device cpu      run on CPU (use 0 for the first CUDA GPU)
--save            save annotated media under runs/classroom/
--show            display annotated frames
--json            emit newline-delimited JSON for integration
```

For all options:

```bash
python inference/detect_and_count.py --help
```

## Training

1. Arrange a YOLO-format dataset with `train/`, `valid/`, and `test/`
   directories next to `data.yaml`, or update the paths in `data.yaml`.
2. Open `training/yolov8_training.ipynb`.
3. Run the cells to install Ultralytics, train, validate, and export the best
   weights.
4. Copy the resulting `best.pt` to `model/best.pt`.

The dataset metadata in `data.yaml` points to the original Roboflow project and
is licensed under CC BY 4.0.


## Contributors

This project was collaboratively developed by:

Sangavi Sriranganathan,
Alberd Rajeevan,
R.H.Nimnada

We worked together as a team to design, develop, and implement this Smart Classroom Edge AI project. Each member contributed to different parts of the project, including data preparation, AI model development, backend/frontend integration, testing, and documentation.
