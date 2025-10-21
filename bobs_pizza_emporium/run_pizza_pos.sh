#!/bin/bash
# Pizza Point of Sales System - Linux/Mac Launcher

echo "================================================"
echo "Pizza Point of Sales System - Quick Start"
echo "================================================"
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed or not in PATH"
    echo "Please install Python 3.6 or higher"
    echo
    exit 1
fi

echo "Python found. Starting Pizza POS System..."
echo
echo "Default login credentials:"
echo "Admin: username=admin, PIN=1234"
echo "Employee: username=employee, PIN=5678"
echo

# Run the application
python3 pizza_pos_app.py

# Check exit status
if [ $? -ne 0 ]; then
    echo
    echo "An error occurred. Press Enter to exit..."
    read
fi
