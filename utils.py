import os
import sys
import platform
import cv2
from pathlib import Path

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def setup_autostart(enable=True):
    """Configure application to start on system boot"""
    app_name = "NoMouse"

    # Get the path to the executable
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        app_path = sys.executable
    else:
        # Running as script
        app_path = sys.argv[0]

    # Make sure we have the absolute path
    app_path = os.path.abspath(app_path)

    system = platform.system()

    if system == "Windows":
        import winreg
        startup_key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0, winreg.KEY_SET_VALUE | winreg.KEY_QUERY_VALUE
        )

        if enable:
            winreg.SetValueEx(startup_key, app_name, 0, winreg.REG_SZ, f'"{app_path}"')
        else:
            try:
                winreg.DeleteValue(startup_key, app_name)
            except FileNotFoundError:
                pass

        winreg.CloseKey(startup_key)

    elif system == "Darwin":  # macOS
        plist_path = os.path.expanduser(f"~/Library/LaunchAgents/{app_name}.plist")

        if enable:
            plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{app_name}</string>
    <key>ProgramArguments</key>
    <array>
        <string>{app_path}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>"""
            os.makedirs(os.path.dirname(plist_path), exist_ok=True)
            with open(plist_path, "w") as f:
                f.write(plist_content)
        else:
            if os.path.exists(plist_path):
                os.remove(plist_path)

    elif system == "Linux":
        autostart_dir = os.path.expanduser("~/.config/autostart")
        desktop_file = os.path.join(autostart_dir, f"{app_name}.desktop")

        if enable:
            desktop_content = f"""[Desktop Entry]
Type=Application
Name={app_name}
Exec={app_path}
Terminal=false
X-GNOME-Autostart-enabled=true
"""
            os.makedirs(autostart_dir, exist_ok=True)
            with open(desktop_file, "w") as f:
                f.write(desktop_content)
        else:
            if os.path.exists(desktop_file):
                os.remove(desktop_file)

    return True

def get_camera_list():
    """Get a list of available cameras"""
    camera_list = []
    index = 0

    # Try to open each camera index until we fail
    while True:
        cap = cv2.VideoCapture(index)
        if not cap.isOpened():
            break

        camera_list.append(f"Camera {index}")
        cap.release()
        index += 1

        # Limit to 10 cameras to avoid infinite loop
        if index >= 10:
            break

    return camera_list
