@echo off
cd /d "%~dp0"
python main.py
if %errorlevel% neq 0 (
    echo.
    echo Something went wrong. Make sure dependencies are installed:
    echo   pip install -r requirements.txt
    pause
)
