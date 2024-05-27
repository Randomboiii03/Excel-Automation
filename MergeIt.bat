@echo off
set "path_to_check=C:\Users\SPM\Desktop\ONLY SAVE FILES HERE\VS Code\Excel-Automation"
cd /d "%path_to_check%"
if exist "%path_to_check%\venv" (
    echo "venv directory exists in %path_to_check%"
    call venv\Scripts\activate.bat
) else (
    echo "venv directory does not exist in %path_to_check%"
    python -m venv venv
    call venv\Scripts\activate.bat
    pip install --upgrade --force-reinstall -r requirements.txt
)
start http://127.0.0.1:8000
python main.py
pause
