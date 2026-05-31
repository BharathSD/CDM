@echo off
setlocal

where python >nul 2>&1
if errorlevel 1 (
  echo ERROR: Python not found in PATH.
  exit /b 1
)

if not exist ".venv\Scripts\activate.bat" (
  python -m venv .venv
)

call .venv\Scripts\activate.bat
pip install -r requirements.txt
python -m reflex run

endlocal
