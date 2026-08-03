@echo off
setlocal
cd /d "%~dp0"

set "PYTHON=env\Scripts\python.exe"
set "YOLO_CONFIG_DIR=%CD%\.cache"
set "MPLCONFIGDIR=%CD%\.cache\matplotlib"
if not exist "%PYTHON%" (
    echo Python environment not found. Run setup.bat first.
    exit /b 1
)

"%PYTHON%" -c "import flask, cv2, torch, ultralytics" >nul 2>&1
if errorlevel 1 (
    echo Required packages are missing or broken. Run setup.bat to repair them.
    exit /b 1
)

echo Starting Edge AI AC Monitor at http://localhost:5000
"%PYTHON%" app.py
