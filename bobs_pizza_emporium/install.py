#!/usr/bin/env python3
"""
Installation script for Pizza Point of Sales Application
"""

import os
import sys
import subprocess
import platform

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 6):
        print("Error: Python 3.6 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    return True

def install_dependencies():
    """Install required dependencies"""
    print("Installing dependencies...")
    try:
        # No external dependencies required - uses only Python standard library
        print("✓ All dependencies are included in Python standard library")
        return True
    except Exception as e:
        print(f"Error installing dependencies: {e}")
        return False

def create_desktop_shortcut():
    """Create desktop shortcut for Windows"""
    if platform.system() == "Windows":
        try:
            import winshell
            from win32com.client import Dispatch
            
            desktop = winshell.desktop()
            path = os.path.join(desktop, "Pizza POS System.lnk")
            target = os.path.join(os.getcwd(), "pizza_pos_app.py")
            
            shell = Dispatch('WScript.Shell')
            shortcut = shell.CreateShortCut(path)
            shortcut.Targetpath = sys.executable
            shortcut.Arguments = f'"{target}"'
            shortcut.WorkingDirectory = os.getcwd()
            shortcut.IconLocation = sys.executable
            shortcut.save()
            
            print("✓ Desktop shortcut created")
            return True
        except ImportError:
            print("Note: Could not create desktop shortcut (winshell not available)")
            return False
    return True

def create_start_menu_entry():
    """Create start menu entry for Windows"""
    if platform.system() == "Windows":
        try:
            import winshell
            
            start_menu = winshell.start_menu()
            programs_folder = os.path.join(start_menu, "Programs")
            pizza_folder = os.path.join(programs_folder, "Pizza POS System")
            
            if not os.path.exists(pizza_folder):
                os.makedirs(pizza_folder)
            
            # Create shortcut in start menu
            shortcut_path = os.path.join(pizza_folder, "Pizza POS System.lnk")
            target = os.path.join(os.getcwd(), "pizza_pos_app.py")
            
            from win32com.client import Dispatch
            shell = Dispatch('WScript.Shell')
            shortcut = shell.CreateShortCut(shortcut_path)
            shortcut.Targetpath = sys.executable
            shortcut.Arguments = f'"{target}"'
            shortcut.WorkingDirectory = os.getcwd()
            shortcut.IconLocation = sys.executable
            shortcut.save()
            
            print("✓ Start menu entry created")
            return True
        except ImportError:
            print("Note: Could not create start menu entry (winshell not available)")
            return False
    return True

def main():
    """Main installation function"""
    print("=" * 50)
    print("Pizza Point of Sales System - Installation")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        input("Press Enter to exit...")
        return False
    
    print(f"✓ Python version: {sys.version}")
    print(f"✓ Platform: {platform.system()} {platform.release()}")
    
    # Install dependencies
    if not install_dependencies():
        input("Press Enter to exit...")
        return False
    
    # Create shortcuts
    create_desktop_shortcut()
    create_start_menu_entry()
    
    print("\n" + "=" * 50)
    print("Installation completed successfully!")
    print("=" * 50)
    print("\nDefault login credentials:")
    print("Admin: username='admin', PIN='1234'")
    print("Employee: username='employee', PIN='5678'")
    print("\nYou can now run the application by:")
    print("1. Double-clicking the desktop shortcut")
    print("2. Finding 'Pizza POS System' in the Start Menu")
    print("3. Running 'python pizza_pos_app.py' from command line")
    
    input("\nPress Enter to exit...")
    return True

if __name__ == "__main__":
    main()
