# Pizza Point of Sales System - Installation Package

## Package Contents

This installation package contains all necessary files for the Pizza Point of Sales System:

### Core Application Files
- `pizza_pos_app.py` - Main application (Python source code)
- `pizza_pos.db` - SQLite database (created automatically on first run)

### Installation and Setup
- `install.py` - Automated installation script
- `requirements.txt` - Python dependencies list
- `README.md` - System documentation and requirements

### Launch Scripts
- `run_pizza_pos.bat` - Windows batch file for easy launching
- `run_pizza_pos.sh` - Linux/Mac shell script for easy launching

### Testing and Documentation
- `test_pizza_pos.py` - Comprehensive test suite
- `USER_MANUAL.md` - Complete user manual and documentation

## Installation Instructions

### For Windows Users
1. Extract all files to a folder (e.g., `C:\PizzaPOS\`)
2. Double-click `run_pizza_pos.bat` to start the application
3. Or run `python install.py` for full installation with shortcuts

### For Linux/Mac Users
1. Extract all files to a folder
2. Make scripts executable: `chmod +x *.sh *.py`
3. Run: `./run_pizza_pos.sh`

### Manual Installation
1. Ensure Python 3.6+ is installed
2. Run: `python pizza_pos_app.py`

## Default Login Credentials

### Administrator Account
- **Username**: admin
- **PIN**: 1234
- **Access**: Full system control, user management, order history

### Employee Account
- **Username**: employee
- **PIN**: 5678
- **Access**: Order processing, menu access
