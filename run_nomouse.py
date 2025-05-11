#!/usr/bin/env python3
"""
NoMouse - Run Script
This script checks for dependencies and runs the NoMouse application.
"""

import os
import sys
import subprocess
import importlib.util

def check_module(module_name):
    """Check if a module is installed"""
    return importlib.util.find_spec(module_name) is not None

def install_module(module_name):
    """Install a module using pip"""
    print(f"Installing {module_name}...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", module_name])
        return True
    except subprocess.CalledProcessError:
        print(f"Failed to install {module_name}.")
        return False

def check_dependencies():
    """Check and install required dependencies"""
    required_modules = [
        "opencv-python",
        "mediapipe",
        "pyautogui",
        "numpy",
        "PyQt6",
        "pillow"
    ]
    
    missing_modules = []
    
    for module in required_modules:
        module_name = module.split(">=")[0]  # Remove version specifier if present
        if not check_module(module_name):
            missing_modules.append(module)
    
    if missing_modules:
        print("Some required modules are missing. Would you like to install them? (y/n)")
        choice = input().lower()
        
        if choice == 'y':
            for module in missing_modules:
                if not install_module(module):
                    print(f"Error: Failed to install {module}. Please install it manually.")
                    return False
            print("All dependencies installed successfully!")
        else:
            print("Cannot run NoMouse without required dependencies.")
            return False
    
    return True

def create_icon():
    """Create application icon if it doesn't exist"""
    if not os.path.exists("assets/icon.png"):
        try:
            if check_module("PIL"):
                subprocess.check_call([sys.executable, "create_icon.py"])
            else:
                print("Warning: PIL not installed. Cannot create icon.")
        except subprocess.CalledProcessError:
            print("Warning: Failed to create icon. The application will still work but may not have an icon.")

def run_application():
    """Run the NoMouse application"""
    try:
        print("Starting NoMouse application...")
        subprocess.check_call([sys.executable, "app.py"])
    except subprocess.CalledProcessError:
        print("Error: Failed to start the application.")
        return False
    except KeyboardInterrupt:
        print("\nApplication terminated by user.")
    
    return True

if __name__ == "__main__":
    print("NoMouse - Hand Gesture Control")
    print("==============================")
    
    if check_dependencies():
        create_icon()
        run_application()
