# Building the Executable

This guide explains how to create a standalone executable for Bob's Pizza Emporium POS System that doesn't require users to have Python installed.

## Prerequisites

1. **Python 3.6+** installed on your system
2. **PyInstaller** - will be installed automatically if needed
3. **Pillow** (for icon creation) - will be installed automatically if needed

## Quick Start

### On macOS/Linux:
```bash
./build_executable.sh
```

### On Windows:
```batch
build_executable.bat
```

## Manual Build Process

If you prefer to build manually:

1. **Install PyInstaller** (if not already installed):
   ```bash
   pip install pyinstaller
   ```

2. **Create the icon** (if not already created):
   ```bash
   python3 create_icon.py
   ```
   This creates `pizza_icon.ico` which will be used as the application icon.

3. **Build the executable**:
   ```bash
   pyinstaller pizza_pos.spec
   ```

4. **Find your executable**:
   - **macOS/Linux**: `dist/BobsPizzaEmporium`
   - **Windows**: `dist/BobsPizzaEmporium.exe`

## What Gets Built

The executable includes:
- All Python code (launch.py, pizza_pos_app.py)
- Python interpreter (embedded)
- All required libraries (tkinter, sqlite3, etc.)
- The pizza icon (pizza_icon.ico)
- Database file (if it exists)

## Distribution

Once built, you can distribute the executable file from the `dist` folder. Users can:
- Double-click to run (no Python installation needed)
- See the pizza icon in the application
- Use all features of the POS system

## Troubleshooting

### Icon not showing
- Make sure `pizza_icon.ico` exists in the project directory
- Run `python3 create_icon.py` to regenerate it

### Build fails
- Ensure all Python files are in the same directory
- Check that PyInstaller is installed: `pip install pyinstaller`
- Try cleaning previous builds: `rm -rf build dist __pycache__`

### Executable is large
- This is normal - it includes the entire Python interpreter
- Typical size: 50-100 MB
- The `--onefile` option bundles everything into a single file

## Notes

- The first run of the executable may be slightly slower as it extracts files
- The database (`pizza_pos.db`) will be created automatically on first run if it doesn't exist
- Default login credentials:
  - Admin: PIN='1234'
  - Employee: PIN='5678'

