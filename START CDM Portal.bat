@echo off
setlocal enabledelayedexpansion
title CDM Portal
color 07
mode con: cols=60 lines=30

:: ─────────────────────────────────────────────────────────
::  CDM Portal – one-click launcher for Windows
::  Double-click this file to start the application.
:: ─────────────────────────────────────────────────────────

cls
echo.
echo  =============================================
echo    CDM Portal - Company Management System
echo  =============================================
echo.

:: ── 1. Python check ──────────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    color 0C
    echo  [!] Python is not installed.
    echo.
    echo  Please install Python 3.11 from:
    echo.
    echo    https://www.python.org/downloads/
    echo.
    echo  IMPORTANT: During installation, tick the box:
    echo    "Add Python to PATH"
    echo.
    echo  After installing Python, run this file again.
    echo.
    pause
    start https://www.python.org/downloads/
    exit /b 1
)

for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PY_VER=%%v
echo  [OK] Python %PY_VER% found.

:: ── 2. Node.js check ─────────────────────────────────────
node --version >nul 2>&1
if errorlevel 1 (
    color 0C
    echo  [!] Node.js is not installed.
    echo.
    echo  Please install Node.js 20 LTS from:
    echo.
    echo    https://nodejs.org/en/download/
    echo.
    echo  Choose the "Windows Installer (.msi)" option.
    echo  After installing Node.js, run this file again.
    echo.
    pause
    start https://nodejs.org/en/download/
    exit /b 1
)

for /f %%v in ('node --version 2^>^&1') do set NODE_VER=%%v
echo  [OK] Node.js %NODE_VER% found.

:: ── 3. Virtual environment setup (first run only) ────────
if not exist ".venv\Scripts\activate.bat" (
    echo.
    echo  [SETUP] First-time setup - creating environment...
    python -m venv .venv
    if errorlevel 1 (
        color 0C
        echo.
        echo  [!] Failed to create Python environment.
        echo      Please contact your support team.
        pause
        exit /b 1
    )
    echo  [OK] Environment created.
)

call .venv\Scripts\activate.bat

:: ── 4. Install / update dependencies ─────────────────────
echo  [SETUP] Checking app dependencies...
pip install -r requirements.txt -q --no-warn-script-location 2>nul
echo  [OK] Dependencies ready.

:: ── 5. Reflex first-time initialisation ──────────────────
if not exist ".web" (
    echo.
    echo  [SETUP] Downloading app components (first run only).
    echo          This may take 3-5 minutes - please wait...
    echo.
    python -m reflex init
    if errorlevel 1 (
        color 0C
        echo.
        echo  [!] App initialisation failed.
        echo      Please contact your support team.
        pause
        exit /b 1
    )
    echo  [OK] App components ready.
)

:: ── 6. Seed test data ─────────────────────────────────────
python scripts\seed_test_data.py >nul 2>&1

:: ── 7. Open browser once the server is ready ─────────────
start /min "" cmd /c "timeout /t 8 /nobreak >nul && start http://localhost:3000"

:: ── 8. Launch ─────────────────────────────────────────────
cls
echo.
echo  =============================================
echo    CDM Portal - Company Management System
echo  =============================================
echo.
echo  Status : RUNNING
echo  URL    : http://localhost:3000
echo.
echo  ── Test login credentials ────────────────────
echo.
echo    Username : admin       Password : Admin@123
echo    Username : editor      Password : Editor@123
echo    Username : viewer      Password : Viewer@123
echo.
echo  ─────────────────────────────────────────────
echo.
echo  Your browser will open automatically.
echo  To stop the app, close this window.
echo.

python -m reflex run --loglevel error

echo.
echo  The application has stopped.
pause
endlocal
