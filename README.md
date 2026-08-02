# smart_classroom_edge-ai
An Edge AI-based Smart Classroom system for real-time occupancy detection, activity recognition, and automated AC control using computer vision, Docker, and a live monitoring dashboard.
# Smart Classroom Edge AI System

A lightweight, privacy-compliant Edge AI prototype that detects classroom occupancy in real time from video feeds, processes inference locally on an edge device, and automatically controls a software-simulated air conditioning system.

---

## 🛠️ Technologies Used

### Machine Learning & Computer Vision
- **YOLOv8** – Real-time person detection model.
- **OpenCV** – Video stream handling, frame extraction, and image processing.
- **Python 3.10** – Primary programming language for backend & inference.
- **Cloud ML Platforms** – Used for model training (Azure ML / Vertex AI / SageMaker / Teachable Machine).

### Backend & API
- **Flask & Flask-CORS** – REST API serving inference output, system telemetry, and MJPEG video streaming.
- **NumPy & Threading** – In-memory video queue processing and rolling statistical tracking.

### Deployment & Containerization
- **Docker & Docker Compose** – Container packaging for local edge deployment.
- **Nginx** – Reverse proxy and static web server.
- **Edge Hardware Targets** – Compatible with Linux Laptops, WSL, Raspberry Pi, NVIDIA Jetson, or mobile Linux hosts.

### Frontend Dashboard
- **HTML5, CSS3, Vanilla JavaScript** – Real-time monitoring UI displaying live occupancy counts, AC status, target temperature, and activity logs.

---
