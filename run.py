#!/usr/bin/env python3
"""
Simple script to run the NoMouse application
"""

import os
import sys
import subprocess

def main():
    print("Starting NoMouse application...")
    
    # Run the application
    try:
        subprocess.run([sys.executable, "app.py"], check=True)
    except KeyboardInterrupt:
        print("\nApplication terminated by user.")
    except subprocess.CalledProcessError as e:
        print(f"\nError running application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
