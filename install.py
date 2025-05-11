#!/usr/bin/env python3
import os
import sys
import subprocess
import platform

def install_dependencies():
    """Install required dependencies for NoMouse"""
    print("Installing NoMouse dependencies...")
    
    # Check if pip is available
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "--version"])
    except subprocess.CalledProcessError:
        print("Error: pip is not installed. Please install pip first.")
        sys.exit(1)
    
    # Install dependencies
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("Dependencies installed successfully!")
    except subprocess.CalledProcessError:
        print("Error: Failed to install dependencies.")
        sys.exit(1)
    
    # Create icon
    try:
        subprocess.check_call([sys.executable, "create_icon.py"])
    except subprocess.CalledProcessError:
        print("Warning: Failed to create icon. The application will still work but may not have an icon.")
    
    print("\nNoMouse is now ready to use!")
    print("Run 'python app.py' to start the application.")

if __name__ == "__main__":
    install_dependencies()
