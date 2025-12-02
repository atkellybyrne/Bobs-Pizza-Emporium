# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Bob's Pizza Emporium POS System
This file configures how PyInstaller builds the executable
"""

import os
import platform

block_cipher = None

# Prepare data files (database will be created on first run if not included)
datas = []
if os.path.exists('pizza_pos.db'):
    datas.append(('pizza_pos.db', '.'))

# Choose icon based on platform (icns for macOS, ico for others)
if platform.system() == 'Darwin' and os.path.exists('pizza_icon.icns'):
    icon_file = 'pizza_icon.icns'
elif os.path.exists('pizza_icon.ico'):
    icon_file = 'pizza_icon.ico'
else:
    icon_file = None

a = Analysis(
    ['launch.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='BobsPizzaEmporium',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Set to False to hide console window (GUI app)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_file,  # Use the pizza icon (icns on macOS, ico on others)
)
