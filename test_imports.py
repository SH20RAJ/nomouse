#!/usr/bin/env python3
"""
Test if all required modules are available
"""

import sys

def check_imports():
    missing_modules = []
    
    # Try to import each required module
    modules = [
        "cv2",
        "mediapipe",
        "pyautogui",
        "numpy",
        "PyQt6",
        "PIL"
    ]
    
    for module in modules:
        try:
            __import__(module)
            print(f"✓ {module} is available")
        except ImportError:
            missing_modules.append(module)
            print(f"✗ {module} is missing")
    
    if missing_modules:
        print("\nMissing modules:")
        for module in missing_modules:
            print(f"  - {module}")
        print("\nPlease install the missing modules with:")
        print(f"{sys.executable} -m pip install -r requirements.txt")
        return False
    else:
        print("\nAll required modules are available!")
        return True

if __name__ == "__main__":
    check_imports()
