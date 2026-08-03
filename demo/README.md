# Edge AI AC Monitor

An AI-driven classroom monitoring system that uses YOLO computer vision to detect occupancy levels and dynamically adjust Air Conditioning (AC) set points in real-time.

---

## 📌 Features

- 📹 **Live AI Camera Processing**: Accepts video uploads and streams processed frames with real-time detection overlays.
- 👥 **Occupancy Detection**: Differentiates between students and cleaners to dynamically calculate active occupancy.
- ❄️ **Smart AC Automation**: Automatically sets AC state and temperature thresholds based on classroom crowd density:
  - **Low Occupancy (≤ 2 people)**: AC **OFF**
  - **Medium Occupancy (3–9 people)**: AC **ON** (24°C)
  - **High Occupancy (10+ people)**: AC **ON** (20°C)
- 📊 **Real-time Monitoring Dashboard**: Clean UI displaying live camera feeds, occupant counts, and AC status.

---

## 📁 Project Structure

```
edge_ai_ac_monitor/
├── app.py                 # Flask web server & YOLO video processor logic
├── smart_classroom.html   # Main dashboard HTML template
├── SCstyle.css            # Custom dashboard styles
├── SC.js                  # Frontend live polling & upload handling
├── Dockerfile             # Container definition
├── docker-compose.yml     # Docker Compose multi-container configuration
├── .dockerignore          # Docker build exclusion list
├── model/
│   └── best.pt            # Trained YOLO object detection model
├── requirements.txt       # Python dependencies
└── uploads/               # Directory for uploaded test videos
```

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.9+ or Docker / Docker Compose
- Git

### 2. Installation & Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/<your-username>/edge_ai_ac_monitor.git
   cd edge_ai_ac_monitor
   ```

2. **Create and activate a virtual environment**:
   - **Windows**:
     ```powershell
     python -m venv venv
     .\venv\Scripts\activate
     ```
   - **Linux / macOS**:
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Verify Model Weights**:
   Ensure your trained YOLO model file `best.pt` is placed inside the `model/` folder:
   ```
   model/best.pt
   ```

---

## 🖥️ Running the Application

### Option A: Local Python Environment
Start the Flask server:
```bash
python app.py
```

### Option B: Docker Container

Using **Docker Compose**:
```bash
docker compose up --build
```

Or using **Docker CLI**:
```bash
# Build Docker image
docker build -t edge_ai_ac_monitor .

# Run Docker container
docker run -p 5000:5000 -v $(pwd)/uploads:/app/uploads edge_ai_ac_monitor
```

---

## 🌐 Accessing the Dashboard

Open your browser and navigate to:
```
http://localhost:5000
```

Click **Upload Video** on the dashboard to test the live AI analytics pipeline on a sample video!

