@echo off
echo ================================================
echo Pizza Point of Sales System - Quick Start
echo ================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.6 or higher from https://python.org
    echo.
    pause
    exit /b 1
)

echo Python found. Starting Pizza POS System...
echo.
echo Default login credentials:
echo Admin: username=admin, PIN=1234
echo Employee: username=employee, PIN=5678
echo.

REM Run the application
python pizza_pos_app.py

REM Keep window open if there's an error
if errorlevel 1 (
    echo.
    echo An error occurred. Press any key to exit...
    pause >nul
)
