@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo Run start_windows.bat first.
  pause
  exit /b 1
)

call ".venv\Scripts\activate.bat"
python -m pip install -r requirements.txt
if errorlevel 1 exit /b 1

pyinstaller --noconfirm --clean --onefile --name AION2-Farmer --add-data "config;config" main.py
if errorlevel 1 (
  echo Build failed.
  pause
  exit /b 1
)

echo EXE created: dist\AION2-Farmer.exe
pause
