# Bob's Pizza Emporium - Standalone Executable

## ✅ Executable Created Successfully!

Your standalone executable has been created and is ready to distribute!

### Location
The executable is located in the `dist` folder:
- **macOS/Linux**: `dist/BobsPizzaEmporium`
- **Windows**: `dist/BobsPizzaEmporium.exe` (when built on Windows)

### Features
- ✅ **No Python Required** - Users don't need Python installed
- ✅ **Pizza Icon** - Custom pizza icon included
- ✅ **Single File** - Everything bundled into one executable
- ✅ **Cross-Platform** - Works on macOS, Windows, and Linux

### Running the Executable

#### macOS/Linux:
```bash
./dist/BobsPizzaEmporium
```

Or simply double-click the file in Finder/File Manager.

#### Windows:
Double-click `BobsPizzaEmporium.exe` in the `dist` folder.

### Default Login Credentials
- **Admin**: PIN='1234'
- **Employee**: PIN='5678'

### Distribution

You can distribute the executable file to users. They can:
1. Download the executable
2. Double-click to run (no installation needed)
3. Start using the POS system immediately

**Note**: The first run may take a few seconds as the application extracts its files.

### Rebuilding the Executable

If you make changes to the code, rebuild the executable:

**macOS/Linux:**
```bash
./build_executable.sh
```

**Windows:**
```batch
build_executable.bat
```

### File Size
The executable is approximately 10-15 MB. This is normal as it includes:
- Python interpreter
- All required libraries (tkinter, sqlite3, etc.)
- Your application code
- The pizza icon

### Troubleshooting

**Executable won't run:**
- On macOS, you may need to allow it in System Preferences > Security & Privacy
- Right-click and select "Open" if you get a security warning

**Icon not showing:**
- The icon should appear in the Dock (macOS) or taskbar
- If not visible, the application is still functional

**Database:**
- The database (`pizza_pos.db`) will be created automatically in the same directory as the executable on first run

### Technical Details

- Built with PyInstaller 6.17.0
- Python 3.14.0
- Icon: pizza_icon.ico (256x256 with multiple sizes)
- Console: Hidden (GUI-only application)

