@echo off
REM Build script for creating the Bob's Pizza Emporium executable (Windows)
REM This script uses PyInstaller to create a standalone executable

echo ============================================================
echo Building Bob's Pizza Emporium Executable
echo ============================================================
echo.

REM Check if PyInstaller is installed
pyinstaller --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: PyInstaller is not installed
    echo Please install it with: pip install pyinstaller
    pause
    exit /b 1
)

REM Check if icon exists
if not exist "pizza_icon.ico" (
    echo WARNING: pizza_icon.ico not found. Creating it now...
    python create_icon.py
    if not exist "pizza_icon.ico" (
        echo ERROR: Failed to create icon. Please create pizza_icon.ico manually.
        pause
        exit /b 1
    )
)

REM Clean previous builds (but keep the spec file)
echo Cleaning previous builds...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist __pycache__ rmdir /s /q __pycache__

REM Check if spec file exists
if not exist "pizza_pos.spec" (
    echo ERROR: pizza_pos.spec not found. Please ensure it exists.
    pause
    exit /b 1
)

REM Build the executable
echo Building executable with PyInstaller...
echo This may take a few minutes...
echo.

pyinstaller pizza_pos.spec

if errorlevel 1 (
    echo.
    echo ============================================================
    echo Build failed!
    echo ============================================================
    echo.
    echo Please check the error messages above.
    pause
    exit /b 1
) else (
    echo.
    echo ============================================================
    echo Build successful!
    echo ============================================================
    echo.
    echo Your executable is located in the 'dist' folder:
    echo   dist\BobsPizzaEmporium.exe
    echo.
    echo You can now distribute this executable to users.
    echo They don't need Python installed to run it!
    echo.
    if exist "dist\BobsPizzaEmporium.exe" (
        echo To test the executable, double-click:
        echo   dist\BobsPizzaEmporium.exe
        echo.
    )
)

pause

