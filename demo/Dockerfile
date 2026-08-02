FROM python:3.12-slim

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    YOLO_CONFIG_DIR=/app/.cache \
    MPLCONFIGDIR=/app/.cache/matplotlib

# Install system dependencies required for OpenCV, FFmpeg, and PyTorch
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./

# Install tested CPU-only PyTorch wheels before the remaining dependencies.
RUN python -m pip install --no-cache-dir \
        torch==2.6.0 torchvision==0.21.0 \
        --index-url https://download.pytorch.org/whl/cpu \
    && python -m pip install --no-cache-dir -r requirements.txt

# Copy essential application source files and model
COPY app.py smart_classroom.html SCstyle.css SC.js ./
COPY model ./model

# Ensure uploads directory exists
RUN mkdir -p /app/uploads /app/.cache/matplotlib

# Expose Flask application port
EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5000/api/live_status', timeout=3)"]

CMD ["python", "app.py"]
