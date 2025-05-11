# NoMouse

[![Visitors](https://api.visitorbadge.io/api/combined?path=https%3A%2F%2Fgithub.com%2Fsh20raj%2Fnomouse%2F&labelColor=%232ccce4&countColor=%23f47373&labelStyle=upper)](https://visitorbadge.io/status?path=https%3A%2F%2Fgithub.com%2Fsh20raj%2Fnomouse%2F)

![NoMouse Icon](./assets/icon.png)

Control your PC without mouse or trackpad using intuitive hand gestures.

## Description

NoMouse is a hands-free computer control system that allows you to navigate and control your computer using hand gestures. This innovative solution eliminates the need for traditional input devices like mouse or trackpad, making computer interaction more intuitive, accessible, and effortless.

## Features

- Precise cursor control using just your index finger
- Natural gesture-based clicking and scrolling
- Advanced smoothing algorithms to reduce shakiness
- Hover-to-click functionality for effortless clicking
- Intuitive pinch gestures for right-click
- Customizable sensitivity and gesture settings
- Modern, sleek user interface
- Interactive tutorial for new users
- Cross-platform compatibility (Windows, macOS, Linux)
- System tray integration for easy access
- Start on boot option for automatic startup
- Multiple camera support

## Gesture Controls

### Mouse Actions
| Action | Gesture | Description |
|--------|---------|-------------|
| 👆 **Move Cursor** | Point with index finger | Extend your index finger while keeping other fingers curled |
| 👌 **Left Click** | Pinch index+thumb | Touch the tips of your thumb and index finger together |
| 👌 **Right Click** | Pinch middle+thumb | Touch the tips of your thumb and middle finger together |
| ✌️ **Scroll** | Two-finger swipe | Extend index and middle fingers in a V shape, move up/down |
| ✊ **Drag & Drop** | Pinch and hold | Pinch index+thumb and hold while moving, release to drop |
| ✌️ **Double Click** | Index+middle together | Extend index and middle fingers close together |

## Installation & Deployment

### For Users: Download Pre-built Releases

1. Go to the [Releases](https://github.com/sh20raj/nomouse/releases) page
2. Download the appropriate package for your operating system:
   - **Windows**: `NoMouse-Windows.zip`
   - **macOS**: `NoMouse-macOS.zip` or `NoMouse.dmg`
   - **Linux**: `NoMouse-Linux.tar.gz` or `.AppImage`
3. Extract the archive (if applicable)
4. Run the application:
   - **Windows**: Double-click `NoMouse.exe`
   - **macOS**: Open `NoMouse.app`
   - **Linux**: Run the `NoMouse` executable or `.AppImage` file

### For Developers: Quick Start

```bash
# Clone the repository
git clone https://github.com/sh20raj/nomouse.git

# Navigate to the project directory
cd nomouse

# Check if all required modules are available
python3 test_imports.py

# Run the application
python3 run.py
```

### For Developers: Manual Installation

```bash
# Clone the repository
git clone https://github.com/sh20raj/nomouse.git

# Navigate to the project directory
cd nomouse

# Install dependencies manually
pip3 install -r requirements.txt

# Run the application directly
python3 app.py
```

### Building from Source (All Platforms)

#### Prerequisites
- Python 3.7 or higher
- pip package manager
- Git (optional, for cloning)

#### Step 1: Install PyInstaller
```bash
pip3 install pyinstaller
```

#### Step 2: Build the Application

**Windows:**
```bash
python -m PyInstaller nomouse.spec
```

**macOS:**
```bash
python3 -m PyInstaller nomouse.spec
```

**Linux:**
```bash
python3 -m PyInstaller nomouse.spec
```

The built application will be available in the `dist` directory.

### Platform-Specific Installation Notes

#### Windows
- Ensure you have the Visual C++ Redistributable installed
- Right-click the executable and select "Run as administrator" for the first run
- To start on boot, use the in-app setting or create a shortcut in the Startup folder

#### macOS
- You may need to allow the app in System Preferences > Security & Privacy
- For camera access, grant permission when prompted
- To start on boot, use the in-app setting or add to Login Items

#### Linux
- Ensure you have the required libraries: `sudo apt-get install python3-opencv python3-pyqt5`
- Make the executable file executable: `chmod +x NoMouse`
- For autostart, use the in-app setting or add to your desktop environment's startup applications

## Usage

1. Launch the NoMouse application.
2. The interactive tutorial will guide you through the basic gestures.
3. Position your hand in front of your camera.
4. Use these intuitive gestures to control your computer:

| Action | Gesture | Tips |
|--------|---------|------|
| 👆 **Move Cursor** | Point with index finger | Keep your hand relaxed and move naturally |
| 👌 **Left Click** | Pinch index+thumb | Quick pinch motion like tapping on a touchscreen |
| 👌 **Right Click** | Pinch middle+thumb | Similar to left click but with middle finger |
| ✌️ **Scroll** | Two-finger V shape | Move hand up/down for scrolling |
| ✊ **Drag & Drop** | Pinch and hold | Hold the pinch while moving, release to drop |
| ✌️ **Double Click** | Index+middle together | Keep fingers close together (not in V shape) |

The gestures are designed to be natural and intuitive, similar to touchscreen and trackpad gestures you're already familiar with.

## Settings

The application provides extensive customization options:

### Gesture Settings
- **Smoothing**: Adjust cursor movement smoothness
- **Stability**: Control jitter reduction sensitivity
- **Click Dwell Time**: Set how long to hold for a click
- **Scroll Sensitivity**: Adjust scrolling speed
- **Pinch Sensitivity**: Fine-tune right-click detection

### Application Settings
- **Camera Selection**: Choose which camera to use
- **Start Minimized**: Launch in system tray
- **Start on Boot**: Run automatically at startup
- **Theme**: Choose between dark and light themes
- **Show Gesture Notifications**: Toggle visual feedback

## System Requirements

- **Operating System**: Windows 10/11, macOS 10.14+, or Linux
- **Hardware**:
  - Webcam (built-in or external)
  - 2GB RAM minimum
  - Dual-core processor or better
- **For Development**:
  - Python 3.7 or higher
  - Dependencies: OpenCV, MediaPipe, PyAutoGUI, PyQt6, NumPy

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

We are open source! Contributions are welcome! Please feel free to submit a Pull Request.

Visit our GitHub repository: https://github.com/sh20raj/nomouse/
