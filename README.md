# NoMouse

Control your PC without mouse or trackpad using hand gestures.

## Description

NoMouse is a hands-free computer control system that allows you to navigate and control your computer using hand gestures. This innovative solution eliminates the need for traditional input devices like mouse or trackpad, making computer interaction more intuitive and accessible.

## Features

- Mouse cursor control through hand gestures
- Click actions (left-click, right-click) using gestures
- Scroll functionality
- Gesture customization options
- Cross-platform compatibility (Windows, macOS, Linux)
- Speed control through thumb gestures
- System tray integration
- Start on boot option
- Camera selection

## Gesture Controls

### Mouse Actions
- Index finger up (only): Left-click
- Middle finger up (only): Right-click
- Move hand: Move cursor
- Thumb closed: Slow cursor movement
- Thumb open: Fast cursor movement
- All fingers up: Scroll mode (move hand up/down to scroll)

## Installation

### From Releases
1. Download the latest release for your operating system from the [Releases](https://github.com/sh20raj/nomouse/releases) page.
2. Extract the archive (if applicable).
3. Run the executable:
   - Windows: Run `NoMouse.exe`
   - macOS: Open `NoMouse.app`
   - Linux: Run `NoMouse` executable

### Quick Start
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

### Manual Installation
```bash
# Install dependencies manually
pip3 install -r requirements.txt

# Run the application directly
python3 app.py
```

### Advanced Installation (Optional)
If you want to build a standalone application:

1. Install PyInstaller:
```bash
pip3 install pyinstaller
```

2. Build the application:
```bash
# On macOS/Linux
python3 -m PyInstaller nomouse.spec

# On Windows
python -m PyInstaller nomouse.spec
```

## Usage

1. Launch the NoMouse application.
2. Position your hand in front of your camera.
3. Move your hand to control the cursor.
4. Use gestures to perform actions:
   - Raise only your index finger to left-click
   - Raise only your middle finger to right-click
   - Raise all fingers to enter scroll mode

## Settings

The application provides several customization options:
- Camera selection
- Movement smoothing
- Scroll sensitivity
- Start minimized option
- Start on boot option

## Requirements

- Python 3.7 or higher (for running from source)
- Webcam
- OpenCV
- MediaPipe
- PyAutoGUI
- PyQt6 (for the GUI)

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
