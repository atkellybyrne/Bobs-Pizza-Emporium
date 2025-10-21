#!/usr/bin/env python3
"""
Pizza Point of Sales System - Universal Launcher
This script ensures the application runs on any system with Python 3.6+
"""

import sys
import os
import subprocess
import platform

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 6):
        print("ERROR: Python 3.6 or higher is required")
        print(f"   Current version: {sys.version}")
        print("\nPlease download and install Python from: https://python.org")
        input("\nPress Enter to exit...")
        return False
    return True

def check_tkinter():
    """Check if tkinter is available"""
    try:
        import tkinter
        return True
    except ImportError:
        print("ERROR: tkinter (GUI library) is not available")
        print("\nSolutions:")
        print("   Windows: tkinter should be included with Python")
        print("   macOS: Install Python from python.org (not Homebrew)")
        print("   Linux: Install python3-tk package")
        print("\nDownload Python from: https://python.org")
        input("\nPress Enter to exit...")
        return False

def check_dependencies():
    """Check all required dependencies"""
    required_modules = ['sqlite3', 'datetime', 'decimal', 'os', 'sys']
    missing_modules = []
    
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing_modules.append(module)
    
    if missing_modules:
        print(f"ERROR: Missing required modules: {', '.join(missing_modules)}")
        print("   This should not happen with a standard Python installation")
        input("\nPress Enter to exit...")
        return False
    
    return True

def run_application():
    """Run the Pizza POS application"""
    try:
        # Import and run the main application
        from pizza_pos_app import PizzaPOSApp
        app = PizzaPOSApp()
        app.run()
    except Exception as e:
        print(f"ERROR: Failed to start application: {e}")
        print("\nTroubleshooting:")
        print("   1. Make sure all files are in the same folder")
        print("   2. Check that pizza_pos_app.py is not corrupted")
        print("   3. Try running: python pizza_pos_app.py")
        input("\nPress Enter to exit...")
        return False
    
    return True

def main():
    """Main launcher function"""
    print("=" * 60)
    print("PIZZA POINT OF SALES SYSTEM - UNIVERSAL LAUNCHER")
    print("=" * 60)
    print()
    
    # Check Python version
    print("Checking Python version...")
    if not check_python_version():
        return False
    print(f"Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro} - OK")
    
    # Check tkinter
    print("Checking GUI library (tkinter)...")
    if not check_tkinter():
        return False
    print("tkinter - OK")
    
    # Check dependencies
    print("Checking dependencies...")
    if not check_dependencies():
        return False
    print("All dependencies - OK")
    
    print("\n" + "=" * 60)
    print("STARTING PIZZA POS SYSTEM")
    print("=" * 60)
    print("\nDefault Login Credentials:")
    print("   Admin: username='admin', PIN='1234'")
    print("   Employee: username='employee', PIN='5678'")
    print("\n" + "=" * 60)
    
    # Run the application
    return run_application()

if __name__ == "__main__":
    try:
        success = main()
        if not success:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nApplication closed by user")
        sys.exit(0)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        input("\nPress Enter to exit...")
        sys.exit(1)
