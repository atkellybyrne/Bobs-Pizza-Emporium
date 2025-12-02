#!/bin/bash
# Build script for creating the Bob's Pizza Emporium executable
# This script uses PyInstaller to create a standalone executable

echo "============================================================"
echo "Building Bob's Pizza Emporium Executable"
echo "============================================================"
echo

# Check if PyInstaller is installed
if ! command -v pyinstaller &> /dev/null; then
    echo "ERROR: PyInstaller is not installed"
    echo "Please install it with: pip install pyinstaller"
    exit 1
fi

# Check if icon exists
if [ ! -f "pizza_icon.ico" ]; then
    echo "WARNING: pizza_icon.ico not found. Creating it now..."
    python3 create_icon.py
    if [ ! -f "pizza_icon.ico" ]; then
        echo "ERROR: Failed to create icon. Please create pizza_icon.ico manually."
        exit 1
    fi
fi

# Clean previous builds (but keep the spec file)
echo "Cleaning previous builds..."
rm -rf build dist __pycache__ 2>/dev/null

# Check if spec file exists
if [ ! -f "pizza_pos.spec" ]; then
    echo "ERROR: pizza_pos.spec not found. Please ensure it exists."
    exit 1
fi

# Build the executable
echo "Building executable with PyInstaller..."
echo "This may take a few minutes..."
echo

pyinstaller pizza_pos.spec

if [ $? -eq 0 ]; then
    echo
    echo "============================================================"
    echo "✓ Build successful!"
    echo "============================================================"
    echo
    echo "Your executable is located in the 'dist' folder:"
    echo "  dist/BobsPizzaEmporium"
    echo
    echo "You can now distribute this executable to users."
    echo "They don't need Python installed to run it!"
    echo
    if [ -f "dist/BobsPizzaEmporium" ]; then
        echo "To test the executable, run:"
        echo "  ./dist/BobsPizzaEmporium"
        echo
    fi
else
    echo
    echo "============================================================"
    echo "✗ Build failed!"
    echo "============================================================"
    echo
    echo "Please check the error messages above."
    exit 1
fi

