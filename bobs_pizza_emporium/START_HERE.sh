#!/bin/bash
# Pizza Point of Sales System - Universal Launcher for Mac/Linux
# This script ensures the application runs on any Mac/Linux system

echo "============================================================"
echo "PIZZA POINT OF SALES SYSTEM - MAC/LINUX LAUNCHER"
echo "============================================================"
echo

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed or not in PATH"
    echo
    echo "Please install Python 3.6+ from:"
    echo "   macOS: https://python.org or 'brew install python3'"
    echo "   Linux: Use your package manager (apt, yum, etc.)"
    echo
    read -p "Press Enter to exit..."
    exit 1
fi

echo "Python 3 found"
echo

# Try to run the universal launcher first
echo "🔍 Running universal launcher..."
python3 launch.py
if [ $? -ne 0 ]; then
    echo
    echo "Trying direct launch..."
    python3 pizza_pos_app.py
    if [ $? -ne 0 ]; then
        echo
        echo "Failed to start application"
        echo
        echo "Troubleshooting:"
        echo "   1. Make sure all files are in the same folder"
        echo "   2. Check that Python 3.6+ is installed"
        echo "   3. Try running: python3 pizza_pos_app.py"
        echo
        read -p "Press Enter to exit..."
        exit 1
    fi
fi

echo
echo "Application closed"
read -p "Press Enter to exit..."
