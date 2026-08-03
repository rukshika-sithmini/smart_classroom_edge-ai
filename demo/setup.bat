@echo off
setlocal
cd /d "%~dp0"

if not exist "env\Scripts\python.exe" (
    py -3.12 -m venv env
    if errorlevel 1 exit /b 1
)

echo Installing application dependencies...
"env\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 exit /b 1
"env\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 exit /b 1

echo Setup complete. Run run_python_venv.bat to start the application.
