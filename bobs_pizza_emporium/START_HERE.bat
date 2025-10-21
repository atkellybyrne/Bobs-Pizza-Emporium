@echo off
REM Pizza Point of Sales System - Windows Universal Launcher
REM This batch file ensures the application runs on any Windows system

echo ============================================================
echo PIZZA POINT OF SALES SYSTEM - WINDOWS LAUNCHER
echo ============================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo.
    echo Please download and install Python from: https://python.org
    echo    Make sure to check "Add Python to PATH" during installation
    echo.
    pause
    exit /b 1
)

echo Python found
echo.

REM Try to run the universal launcher first
echo 🔍 Running universal launcher...
python launch.py
if errorlevel 1 (
    echo.
    echo 🔄 Trying direct launch...
    python pizza_pos_app.py
    if errorlevel 1 (
        echo.
        echo Failed to start application
        echo.
        echo Troubleshooting:
        echo    1. Make sure all files are in the same folder
        echo    2. Check that Python 3.6+ is installed
        echo    3. Try running: python pizza_pos_app.py
        echo.
        pause
        exit /b 1
    )
)

echo.
echo Application closed
pause
