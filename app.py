import sys
import os
import cv2
import threading
import time
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                            QHBoxLayout, QPushButton, QLabel, QSlider, QCheckBox,
                            QComboBox, QSystemTrayIcon, QMenu, QTabWidget,
                            QGroupBox, QRadioButton, QFrame, QSizePolicy,
                            QSpacerItem, QDialog, QWizard, QWizardPage, QToolTip,
                            QProgressBar, QStyleFactory)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, QSize, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QIcon, QImage, QPixmap, QCloseEvent, QColor, QPalette, QFont, QFontDatabase, QCursor

from controller import HandGestureController
from settings import Settings
import utils

class VideoThread(QThread):
    change_pixmap_signal = pyqtSignal(QImage)
    status_signal = pyqtSignal(str)
    fps_signal = pyqtSignal(float)

    def __init__(self, camera_index=0):
        super().__init__()
        self.camera_index = camera_index
        self.running = True
        self.controller = None
        self.settings = None
        self.frame_count = 0
        self.fps = 0
        self.last_fps_time = time.time()
        self.processing_enabled = True

    def set_controller(self, controller):
        self.controller = controller

    def set_settings(self, settings):
        self.settings = settings

    def set_camera_index(self, index):
        self.camera_index = index

    def toggle_processing(self, enabled):
        self.processing_enabled = enabled

    def run(self):
        # Try to open camera with specified settings
        cap = cv2.VideoCapture(self.camera_index)

        # Set camera properties for better performance
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 30)

        if not cap.isOpened():
            self.status_signal.emit("Error: Could not open camera")
            return

        self.status_signal.emit("Camera connected")

        # Performance tracking
        frame_time = time.time()
        processing_times = []

        while self.running:
            # Measure frame processing time
            start_time = time.time()

            # Read frame
            ret, frame = cap.read()
            if not ret:
                self.status_signal.emit("Error: Failed to read frame")
                break

            # Flip frame horizontally for natural movement
            frame = cv2.flip(frame, 1)

            # Process frame if enabled
            if self.controller and self.settings and self.settings.get('enabled') and self.processing_enabled:
                # Process frame and detect hands
                results = self.controller.process_frame(frame)

                # Draw hand landmarks
                self.controller.draw_landmarks(frame, results)

                # Process hand gestures and control mouse
                if results.multi_hand_landmarks:
                    hand_landmarks = results.multi_hand_landmarks[0]
                    gesture_state = self.controller.get_gesture(hand_landmarks)
                    self.controller.control_mouse(hand_landmarks, gesture_state)

            # Add FPS counter
            self.frame_count += 1
            if time.time() - self.last_fps_time > 1.0:
                self.fps = self.frame_count / (time.time() - self.last_fps_time)
                self.frame_count = 0
                self.last_fps_time = time.time()
                self.fps_signal.emit(self.fps)

            # Add FPS text to frame
            cv2.putText(frame, f"FPS: {self.fps:.1f}", (10, frame.shape[0] - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

            # Convert to Qt format for display
            rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)

            # Emit signal with the image
            self.change_pixmap_signal.emit(qt_image)

            # Calculate processing time
            process_time = time.time() - start_time
            processing_times.append(process_time)
            if len(processing_times) > 100:
                processing_times.pop(0)

            # Adaptive sleep to maintain target frame rate
            target_frame_time = 1.0 / 30  # Target 30 FPS
            sleep_time = max(0, target_frame_time - process_time)
            if sleep_time > 0:
                time.sleep(sleep_time)

        cap.release()
        self.status_signal.emit("Camera disconnected")

    def stop(self):
        self.running = False
        self.wait()


class TutorialWizard(QWizard):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("NoMouse Tutorial")
        self.setWizardStyle(QWizard.WizardStyle.ModernStyle)
        self.setMinimumSize(700, 500)

        # Apply styling
        self.setStyleSheet("""
            QWizard {
                background-color: #2D2D30;
                color: #FFFFFF;
            }
            QWizardPage {
                background-color: #2D2D30;
                color: #FFFFFF;
            }
            QLabel {
                color: #FFFFFF;
                font-size: 14px;
            }
            QPushButton {
                background-color: #0078D7;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #1C97EA;
            }
            QPushButton:pressed {
                background-color: #00559B;
            }
        """)

        # Set button text
        self.setButtonText(QWizard.WizardButton.BackButton, "Back")
        self.setButtonText(QWizard.WizardButton.NextButton, "Next")
        self.setButtonText(QWizard.WizardButton.FinishButton, "Finish")
        self.setButtonText(QWizard.WizardButton.CancelButton, "Skip Tutorial")

        # Add pages
        self.add_intro_page()
        self.add_cursor_page()
        self.add_click_page()
        self.add_right_click_page()
        self.add_scroll_page()
        self.add_drag_page()
        self.add_double_click_page()
        self.add_finish_page()

    def add_intro_page(self):
        page = QWizardPage()
        page.setTitle("Welcome to NoMouse")

        layout = QVBoxLayout(page)

        intro_label = QLabel(
            "NoMouse allows you to control your computer using hand gestures, "
            "without needing a physical mouse or trackpad.\n\n"
            "This tutorial will guide you through the basic gestures and features."
        )
        intro_label.setWordWrap(True)

        image_label = QLabel()
        pixmap = QPixmap(utils.resource_path("assets/icon.png"))
        if not pixmap.isNull():
            pixmap = pixmap.scaled(200, 200, Qt.AspectRatioMode.KeepAspectRatio)
            image_label.setPixmap(pixmap)
            image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(intro_label)
        layout.addWidget(image_label)
        layout.addStretch()

        self.addPage(page)

    def add_cursor_page(self):
        page = QWizardPage()
        page.setTitle("👆 Moving the Cursor")

        layout = QVBoxLayout(page)

        cursor_label = QLabel(
            "To move the cursor, point with your index finger.\n\n"
            "Extend your index finger while keeping other fingers curled. "
            "The cursor follows the tip of your index finger. Move your hand "
            "naturally as if you were pointing at the screen.\n\n"
            "This gesture mimics the natural pointing motion we use in everyday life. "
            "The movement has been optimized with advanced smoothing algorithms "
            "to reduce shakiness and make precise positioning easier."
        )
        cursor_label.setWordWrap(True)

        # Add image placeholder
        image_label = QLabel()
        image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        image_label.setMinimumHeight(150)
        image_label.setStyleSheet("background-color: #1E1E1E; border-radius: 8px;")
        image_label.setText("👆 Point with Index Finger")

        layout.addWidget(cursor_label)
        layout.addWidget(image_label)
        layout.addStretch()

        self.addPage(page)

    def add_click_page(self):
        page = QWizardPage()
        page.setTitle("👌 Left-Click")

        layout = QVBoxLayout(page)

        click_label = QLabel(
            "To perform a left-click, pinch your thumb and index finger together.\n\n"
            "Bring your thumb and index finger tips together in a pinching motion, "
            "similar to how you would tap on a touchscreen. "
            "A visual indicator will show the pinch being recognized.\n\n"
            "This gesture is intuitive and mimics the natural tapping motion "
            "we use with touchscreens and trackpads."
        )
        click_label.setWordWrap(True)

        # Add image placeholder
        image_label = QLabel()
        image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        image_label.setMinimumHeight(150)
        image_label.setStyleSheet("background-color: #1E1E1E; border-radius: 8px;")
        image_label.setText("👌 Pinch Index+Thumb to Left-Click")

        layout.addWidget(click_label)
        layout.addWidget(image_label)
        layout.addStretch()

        self.addPage(page)

    def add_right_click_page(self):
        page = QWizardPage()
        page.setTitle("👌 Right-Click")

        layout = QVBoxLayout(page)

        right_click_label = QLabel(
            "To perform a right-click, pinch your thumb and middle finger together.\n\n"
            "Bring your thumb and middle finger tips together in a pinching motion. "
            "This is similar to the left-click gesture but uses your middle finger instead.\n\n"
            "This gesture provides a natural alternative to the left-click, "
            "making it easy to distinguish between the two actions."
        )
        right_click_label.setWordWrap(True)

        # Add image placeholder
        image_label = QLabel()
        image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        image_label.setMinimumHeight(150)
        image_label.setStyleSheet("background-color: #1E1E1E; border-radius: 8px;")
        image_label.setText("👌 Pinch Middle+Thumb to Right-Click")

        layout.addWidget(right_click_label)
        layout.addWidget(image_label)
        layout.addStretch()

        self.addPage(page)

    def add_scroll_page(self):
        page = QWizardPage()
        page.setTitle("✌️ Scrolling")

        layout = QVBoxLayout(page)

        scroll_label = QLabel(
            "To scroll, make a peace sign with your index and middle fingers.\n\n"
            "Extend your index and middle fingers in a V shape while keeping other fingers curled. "
            "Then move your hand up and down to scroll. Moving your hand up scrolls up, "
            "and moving down scrolls down.\n\n"
            "This gesture is similar to the two-finger scroll on a trackpad, "
            "making it intuitive for users familiar with touchpad gestures."
        )
        scroll_label.setWordWrap(True)

        # Add image placeholder
        image_label = QLabel()
        image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        image_label.setMinimumHeight(150)
        image_label.setStyleSheet("background-color: #1E1E1E; border-radius: 8px;")
        image_label.setText("✌️ Two-Finger V Shape to Scroll")

        layout.addWidget(scroll_label)
        layout.addWidget(image_label)
        layout.addStretch()

        self.addPage(page)

    def add_drag_page(self):
        page = QWizardPage()
        page.setTitle("✊ Dragging")

        layout = QVBoxLayout(page)

        drag_label = QLabel(
            "To drag items, pinch your thumb and index finger and hold.\n\n"
            "First, position the cursor over the item you want to drag. "
            "Then pinch your thumb and index finger together and hold while moving your hand. "
            "Release the pinch to drop the item.\n\n"
            "This gesture mimics the natural 'grab and move' motion we use when "
            "manipulating physical objects, making it intuitive and easy to learn."
        )
        drag_label.setWordWrap(True)

        # Add image placeholder
        image_label = QLabel()
        image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        image_label.setMinimumHeight(150)
        image_label.setStyleSheet("background-color: #1E1E1E; border-radius: 8px;")
        image_label.setText("✊ Pinch and Hold to Drag")

        layout.addWidget(drag_label)
        layout.addWidget(image_label)
        layout.addStretch()

        self.addPage(page)

    def add_double_click_page(self):
        page = QWizardPage()
        page.setTitle("✌️ Double-Click")

        layout = QVBoxLayout(page)

        double_click_label = QLabel(
            "To perform a double-click, extend your index and middle fingers close together.\n\n"
            "Extend your index and middle fingers while keeping them close together (not in a V shape). "
            "This gesture is distinct from the scrolling gesture where the fingers form a V.\n\n"
            "Double-clicking is useful for opening files and folders or selecting words in text."
        )
        double_click_label.setWordWrap(True)

        # Add image placeholder
        image_label = QLabel()
        image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        image_label.setMinimumHeight(150)
        image_label.setStyleSheet("background-color: #1E1E1E; border-radius: 8px;")
        image_label.setText("✌️ Index+Middle Together for Double-Click")

        layout.addWidget(double_click_label)
        layout.addWidget(image_label)
        layout.addStretch()

        self.addPage(page)

    def add_finish_page(self):
        page = QWizardPage()
        page.setTitle("Ready to Go!")

        layout = QVBoxLayout(page)

        finish_label = QLabel(
            "You're now ready to use NoMouse!\n\n"
            "Remember, you can access settings and customize the experience "
            "through the settings tab. You can also access this tutorial again "
            "from the Help menu.\n\n"
            "Enjoy using your computer without a mouse!"
        )
        finish_label.setWordWrap(True)

        layout.addWidget(finish_label)
        layout.addStretch()

        self.addPage(page)


class NoMouseApp(QMainWindow):
    def __init__(self):
        super().__init__()

        # Set application style
        self.setup_style()

        # Load settings
        self.settings_manager = Settings()

        # Initialize controller
        self.controller = HandGestureController(self.settings_manager.current)

        # Setup UI
        self.init_ui()

        # Setup video thread
        self.video_thread = VideoThread(self.settings_manager.get('camera_index', 0))
        self.video_thread.set_controller(self.controller)
        self.video_thread.set_settings(self.settings_manager.current)
        self.video_thread.change_pixmap_signal.connect(self.update_image)
        self.video_thread.status_signal.connect(self.update_status)
        self.video_thread.fps_signal.connect(self.update_fps)

        # Start video thread if enabled
        if self.settings_manager.get('enabled'):
            self.video_thread.start()

        # Start minimized if configured
        if self.settings_manager.get('start_minimized'):
            self.hide()

        # Show tutorial for first-time users
        if self.settings_manager.get('show_tutorial', True):
            self.show_tutorial()
            self.settings_manager.set('show_tutorial', False)

    def setup_style(self):
        """Set up application style and theme"""
        # Get the application instance
        app = QApplication.instance()

        # Set application font (use system default font)
        app.setFont(app.font())

        # Set dark theme palette
        dark_palette = QPalette()
        dark_palette.setColor(QPalette.ColorRole.Window, QColor(45, 45, 48))
        dark_palette.setColor(QPalette.ColorRole.WindowText, QColor(255, 255, 255))
        dark_palette.setColor(QPalette.ColorRole.Base, QColor(30, 30, 30))
        dark_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(255, 255, 255))
        dark_palette.setColor(QPalette.ColorRole.ToolTipText, QColor(255, 255, 255))
        dark_palette.setColor(QPalette.ColorRole.Text, QColor(255, 255, 255))
        dark_palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ColorRole.ButtonText, QColor(255, 255, 255))
        dark_palette.setColor(QPalette.ColorRole.BrightText, QColor(0, 120, 215))
        dark_palette.setColor(QPalette.ColorRole.Link, QColor(0, 120, 215))
        dark_palette.setColor(QPalette.ColorRole.Highlight, QColor(0, 120, 215))
        dark_palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))

        # Apply palette
        app.setPalette(dark_palette)

        # Set stylesheet for custom styling
        app.setStyle(QStyleFactory.create("Fusion"))

        # Additional stylesheet for controls
        app.setStyleSheet("""
            QPushButton {
                background-color: #0078D7;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #1C97EA;
            }
            QPushButton:pressed {
                background-color: #00559B;
            }
            QPushButton:disabled {
                background-color: #555555;
                color: #888888;
            }

            QSlider::groove:horizontal {
                border: 1px solid #999999;
                height: 8px;
                background: #3C3C3C;
                margin: 2px 0;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #0078D7;
                border: none;
                width: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }
            QSlider::handle:horizontal:hover {
                background: #1C97EA;
            }

            QTabWidget::pane {
                border: 1px solid #555555;
                background-color: #2D2D30;
            }
            QTabBar::tab {
                background-color: #3C3C3C;
                color: #CCCCCC;
                padding: 8px 16px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #0078D7;
                color: white;
            }
            QTabBar::tab:hover:!selected {
                background-color: #505050;
            }

            QCheckBox {
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }

            QGroupBox {
                border: 1px solid #555555;
                border-radius: 4px;
                margin-top: 16px;
                padding-top: 16px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 5px;
                color: #CCCCCC;
            }
        """)

    def show_tutorial(self):
        """Show the tutorial wizard"""
        tutorial = TutorialWizard(self)
        tutorial.exec()

    def init_ui(self):
        # Main window setup
        self.setWindowTitle('NoMouse - Hand Gesture Control')
        self.setGeometry(100, 100, 1000, 700)
        self.setMinimumSize(800, 600)

        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Create header with logo and title
        header_layout = QHBoxLayout()

        # Logo
        logo_label = QLabel()
        pixmap = QPixmap(utils.resource_path("assets/icon.png"))
        if not pixmap.isNull():
            pixmap = pixmap.scaled(48, 48, Qt.AspectRatioMode.KeepAspectRatio)
            logo_label.setPixmap(pixmap)

        # Title
        title_label = QLabel("NoMouse")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #0078D7;")

        # Status label
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #AAAAAA;")

        # FPS counter
        self.fps_label = QLabel("FPS: 0")
        self.fps_label.setStyleSheet("color: #AAAAAA;")

        header_layout.addWidget(logo_label)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.status_label)
        header_layout.addWidget(self.fps_label)

        main_layout.addLayout(header_layout)

        # Create tabs
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        main_layout.addWidget(self.tabs)

        # Main tab
        self.setup_main_tab()

        # Settings tab
        self.setup_settings_tab()

        # Help tab
        self.setup_help_tab()

        # System tray setup
        self.setup_system_tray()

    def setup_main_tab(self):
        """Set up the main tab with video feed and controls"""
        main_tab = QWidget()
        main_tab_layout = QVBoxLayout(main_tab)
        main_tab_layout.setContentsMargins(0, 0, 0, 0)

        # Create a frame for the video display
        video_frame = QFrame()
        video_frame.setFrameShape(QFrame.Shape.StyledPanel)
        video_frame.setStyleSheet("background-color: #1E1E1E; border-radius: 8px;")
        video_layout = QVBoxLayout(video_frame)

        # Video display
        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setMinimumSize(640, 480)
        self.video_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.video_label.setStyleSheet("background-color: #1E1E1E; border-radius: 8px;")
        video_layout.addWidget(self.video_label)

        main_tab_layout.addWidget(video_frame)

        # Controls panel
        controls_frame = QFrame()
        controls_frame.setFrameShape(QFrame.Shape.StyledPanel)
        controls_frame.setStyleSheet("background-color: #2D2D30; border-radius: 8px; padding: 10px;")
        controls_layout = QHBoxLayout(controls_frame)

        # Enable/Disable button
        self.toggle_button = QPushButton('Disable' if self.settings_manager.get('enabled') else 'Enable')
        self.toggle_button.setMinimumWidth(120)
        self.toggle_button.clicked.connect(self.toggle_gesture_control)

        # Pause/Resume button
        self.pause_button = QPushButton('Pause')
        self.pause_button.setMinimumWidth(120)
        self.pause_button.clicked.connect(self.toggle_processing)

        # Tutorial button
        tutorial_button = QPushButton('Tutorial')
        tutorial_button.setMinimumWidth(120)
        tutorial_button.clicked.connect(self.show_tutorial)

        # Add buttons to layout
        controls_layout.addWidget(self.toggle_button)
        controls_layout.addWidget(self.pause_button)
        controls_layout.addStretch()
        controls_layout.addWidget(tutorial_button)

        main_tab_layout.addWidget(controls_frame)

        # Add tab
        self.tabs.addTab(main_tab, 'Main')

    def setup_settings_tab(self):
        """Set up the settings tab with all configuration options"""
        settings_tab = QWidget()
        settings_layout = QVBoxLayout(settings_tab)
        settings_layout.setSpacing(20)

        # Camera settings group
        camera_group = QGroupBox("Camera Settings")
        camera_layout = QVBoxLayout(camera_group)

        # Camera selection
        camera_selector_layout = QHBoxLayout()
        camera_selector_layout.addWidget(QLabel('Camera:'))
        self.camera_combo = QComboBox()

        # Add camera options
        for i in range(5):  # Try first 5 camera indices
            self.camera_combo.addItem(f'Camera {i}')

        self.camera_combo.setCurrentIndex(self.settings_manager.get('camera_index', 0))
        self.camera_combo.currentIndexChanged.connect(self.change_camera)
        camera_selector_layout.addWidget(self.camera_combo)
        camera_selector_layout.addStretch()

        camera_layout.addLayout(camera_selector_layout)
        settings_layout.addWidget(camera_group)

        # Gesture settings group
        gesture_group = QGroupBox("Gesture Settings")
        gesture_layout = QVBoxLayout(gesture_group)

        # Smoothing factor
        smoothing_layout = QHBoxLayout()
        smoothing_layout.addWidget(QLabel('Smoothing:'))
        self.smoothing_slider = QSlider(Qt.Orientation.Horizontal)
        self.smoothing_slider.setRange(1, 10)
        self.smoothing_slider.setValue(int(self.settings_manager.get('smoothing_factor', 0.8) * 10))
        self.smoothing_slider.valueChanged.connect(self.update_smoothing)
        self.smoothing_value_label = QLabel(f"{self.smoothing_slider.value() / 10:.1f}")
        smoothing_layout.addWidget(self.smoothing_slider)
        smoothing_layout.addWidget(self.smoothing_value_label)
        gesture_layout.addLayout(smoothing_layout)

        # Stability threshold
        stability_layout = QHBoxLayout()
        stability_layout.addWidget(QLabel('Stability:'))
        self.stability_slider = QSlider(Qt.Orientation.Horizontal)
        self.stability_slider.setRange(1, 20)
        self.stability_slider.setValue(self.settings_manager.get('stability_threshold', 5))
        self.stability_slider.valueChanged.connect(self.update_stability)
        self.stability_value_label = QLabel(f"{self.stability_slider.value()}")
        stability_layout.addWidget(self.stability_slider)
        stability_layout.addWidget(self.stability_value_label)
        gesture_layout.addLayout(stability_layout)

        # Dwell time
        dwell_layout = QHBoxLayout()
        dwell_layout.addWidget(QLabel('Click Dwell Time:'))
        self.dwell_slider = QSlider(Qt.Orientation.Horizontal)
        self.dwell_slider.setRange(5, 20)
        self.dwell_slider.setValue(int(self.settings_manager.get('dwell_time', 0.8) * 10))
        self.dwell_slider.valueChanged.connect(self.update_dwell_time)
        self.dwell_value_label = QLabel(f"{self.dwell_slider.value() / 10:.1f}s")
        dwell_layout.addWidget(self.dwell_slider)
        dwell_layout.addWidget(self.dwell_value_label)
        gesture_layout.addLayout(dwell_layout)

        # Scroll sensitivity
        scroll_layout = QHBoxLayout()
        scroll_layout.addWidget(QLabel('Scroll Sensitivity:'))
        self.scroll_slider = QSlider(Qt.Orientation.Horizontal)
        self.scroll_slider.setRange(1, 10)
        self.scroll_slider.setValue(self.settings_manager.get('scroll_sensitivity', 5))
        self.scroll_slider.valueChanged.connect(self.update_scroll_sensitivity)
        self.scroll_value_label = QLabel(f"{self.scroll_slider.value()}")
        scroll_layout.addWidget(self.scroll_slider)
        scroll_layout.addWidget(self.scroll_value_label)
        gesture_layout.addLayout(scroll_layout)

        # Pinch threshold
        pinch_layout = QHBoxLayout()
        pinch_layout.addWidget(QLabel('Pinch Sensitivity:'))
        self.pinch_slider = QSlider(Qt.Orientation.Horizontal)
        self.pinch_slider.setRange(5, 20)
        self.pinch_slider.setValue(int(self.settings_manager.get('pinch_threshold', 0.1) * 100))
        self.pinch_slider.valueChanged.connect(self.update_pinch_threshold)
        self.pinch_value_label = QLabel(f"{self.pinch_slider.value() / 100:.2f}")
        pinch_layout.addWidget(self.pinch_slider)
        pinch_layout.addWidget(self.pinch_value_label)
        gesture_layout.addLayout(pinch_layout)

        settings_layout.addWidget(gesture_group)

        # Application settings group
        app_group = QGroupBox("Application Settings")
        app_layout = QVBoxLayout(app_group)

        # Start minimized option
        self.minimized_checkbox = QCheckBox('Start Minimized')
        self.minimized_checkbox.setChecked(self.settings_manager.get('start_minimized', False))
        self.minimized_checkbox.stateChanged.connect(self.toggle_start_minimized)
        app_layout.addWidget(self.minimized_checkbox)

        # Start on boot option
        self.autostart_checkbox = QCheckBox('Start on System Boot')
        self.autostart_checkbox.setChecked(self.settings_manager.get('start_on_boot', False))
        self.autostart_checkbox.stateChanged.connect(self.toggle_start_on_boot)
        app_layout.addWidget(self.autostart_checkbox)

        # Show gestures option
        self.gestures_checkbox = QCheckBox('Show Gesture Notifications')
        self.gestures_checkbox.setChecked(self.settings_manager.get('show_gestures', True))
        self.gestures_checkbox.stateChanged.connect(self.toggle_show_gestures)
        app_layout.addWidget(self.gestures_checkbox)

        # Theme selection
        theme_layout = QHBoxLayout()
        theme_layout.addWidget(QLabel('Theme:'))
        self.theme_combo = QComboBox()
        self.theme_combo.addItem('Dark')
        self.theme_combo.addItem('Light')
        self.theme_combo.setCurrentText(self.settings_manager.get('theme', 'Dark').capitalize())
        self.theme_combo.currentTextChanged.connect(self.change_theme)
        theme_layout.addWidget(self.theme_combo)
        theme_layout.addStretch()
        app_layout.addLayout(theme_layout)

        settings_layout.addWidget(app_group)

        # Reset button
        reset_layout = QHBoxLayout()
        reset_button = QPushButton('Reset to Defaults')
        reset_button.clicked.connect(self.reset_settings)
        reset_layout.addStretch()
        reset_layout.addWidget(reset_button)
        settings_layout.addLayout(reset_layout)

        # Add spacer at the bottom
        settings_layout.addStretch()

        # Add tab
        self.tabs.addTab(settings_tab, 'Settings')

    def setup_help_tab(self):
        """Set up the help tab with tutorial and information"""
        help_tab = QWidget()
        help_layout = QVBoxLayout(help_tab)

        # Help content
        help_frame = QFrame()
        help_frame.setFrameShape(QFrame.Shape.StyledPanel)
        help_frame.setStyleSheet("background-color: #2D2D30; border-radius: 8px; padding: 20px;")
        help_content_layout = QVBoxLayout(help_frame)

        # Title
        help_title = QLabel("NoMouse Help")
        help_title.setStyleSheet("font-size: 20px; font-weight: bold; color: #0078D7;")
        help_content_layout.addWidget(help_title)

        # Description
        help_desc = QLabel(
            "NoMouse allows you to control your computer using hand gestures, "
            "without needing a physical mouse or trackpad."
        )
        help_desc.setWordWrap(True)
        help_content_layout.addWidget(help_desc)

        # Gesture guide
        gesture_title = QLabel("Gesture Guide")
        gesture_title.setStyleSheet("font-size: 16px; font-weight: bold; margin-top: 20px;")
        help_content_layout.addWidget(gesture_title)

        # Gesture list with emojis
        gestures = [
            ("👆 Move Cursor", "Point with your index finger (other fingers curled)"),
            ("👌 Left Click", "Pinch your thumb and index finger together"),
            ("👌 Right Click", "Pinch your thumb and middle finger together"),
            ("✌️ Scroll", "Make a peace sign (V shape) and move up/down"),
            ("✊ Drag & Drop", "Pinch index+thumb and hold while moving, release to drop"),
            ("✌️ Double Click", "Extend index and middle fingers close together")
        ]

        for title, desc in gestures:
            gesture_layout = QHBoxLayout()
            gesture_name = QLabel(title)
            gesture_name.setStyleSheet("font-weight: bold; min-width: 100px;")
            gesture_desc = QLabel(desc)
            gesture_desc.setWordWrap(True)

            gesture_layout.addWidget(gesture_name)
            gesture_layout.addWidget(gesture_desc)
            help_content_layout.addLayout(gesture_layout)

        # Tutorial button
        tutorial_button = QPushButton("Start Tutorial")
        tutorial_button.clicked.connect(self.show_tutorial)
        help_content_layout.addWidget(tutorial_button, alignment=Qt.AlignmentFlag.AlignCenter)

        # Version info
        version_label = QLabel("NoMouse v1.0.0")
        version_label.setStyleSheet("color: #AAAAAA; margin-top: 20px;")
        help_content_layout.addWidget(version_label, alignment=Qt.AlignmentFlag.AlignRight)

        help_layout.addWidget(help_frame)

        # Add tab
        self.tabs.addTab(help_tab, 'Help')

    def setup_system_tray(self):
        # Create system tray icon
        self.tray_icon = QSystemTrayIcon(self)

        # Try to set icon, use default if not available
        icon_path = utils.resource_path('assets/icon.png')
        if os.path.exists(icon_path):
            self.tray_icon.setIcon(QIcon(icon_path))
        else:
            # Use a default icon from Qt
            self.tray_icon.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_ComputerIcon))

        # Create tray menu
        tray_menu = QMenu()

        # Add actions
        show_action = tray_menu.addAction('Show')
        show_action.triggered.connect(self.show)

        toggle_action = tray_menu.addAction('Disable' if self.settings_manager.get('enabled') else 'Enable')
        toggle_action.triggered.connect(self.toggle_gesture_control)
        self.tray_toggle_action = toggle_action

        quit_action = tray_menu.addAction('Quit')
        quit_action.triggered.connect(self.quit_application)

        # Set the menu
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

        # Connect signals
        self.tray_icon.activated.connect(self.tray_icon_activated)

    def tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            if self.isVisible():
                self.hide()
            else:
                self.show()
                self.activateWindow()

    def update_image(self, image):
        """Update the video display with the latest frame"""
        self.video_label.setPixmap(QPixmap.fromImage(image).scaled(
            self.video_label.width(), self.video_label.height(),
            Qt.AspectRatioMode.KeepAspectRatio))

    def update_status(self, status):
        """Update the status label"""
        self.status_label.setText(status)

    def update_fps(self, fps):
        """Update the FPS counter"""
        self.fps_label.setText(f"FPS: {fps:.1f}")

    def toggle_gesture_control(self):
        """Enable or disable gesture control"""
        enabled = not self.settings_manager.get('enabled')
        self.settings_manager.set('enabled', enabled)

        # Update controller
        self.controller.update_settings({'enabled': enabled})
        self.video_thread.set_settings(self.settings_manager.current)

        # Update UI
        self.toggle_button.setText('Disable' if enabled else 'Enable')
        self.tray_toggle_action.setText('Disable' if enabled else 'Enable')

        # Start/stop video thread
        if enabled and not self.video_thread.isRunning():
            self.video_thread.start()
        elif not enabled and self.video_thread.isRunning():
            # Don't stop the thread, just disable control
            pass

    def toggle_processing(self):
        """Pause or resume processing (but keep video feed)"""
        processing_enabled = not getattr(self.video_thread, 'processing_enabled', True)
        self.video_thread.toggle_processing(processing_enabled)

        # Update UI
        self.pause_button.setText('Pause' if processing_enabled else 'Resume')

    def change_camera(self, index):
        """Change the camera source"""
        self.settings_manager.set('camera_index', index)

        # Restart video thread with new camera
        if self.video_thread.isRunning():
            self.video_thread.stop()

        self.video_thread = VideoThread(index)
        self.video_thread.set_controller(self.controller)
        self.video_thread.set_settings(self.settings_manager.current)
        self.video_thread.change_pixmap_signal.connect(self.update_image)
        self.video_thread.status_signal.connect(self.update_status)
        self.video_thread.fps_signal.connect(self.update_fps)

        if self.settings_manager.get('enabled'):
            self.video_thread.start()

    def update_smoothing(self):
        """Update smoothing factor setting"""
        value = self.smoothing_slider.value() / 10.0
        self.settings_manager.set('smoothing_factor', value)

        # Update label
        self.smoothing_value_label.setText(f"{value:.1f}")

        # Update controller
        self.controller.update_settings({'smoothing_factor': value})

    def update_stability(self):
        """Update stability threshold setting"""
        value = self.stability_slider.value()
        self.settings_manager.set('stability_threshold', value)

        # Update label
        self.stability_value_label.setText(f"{value}")

        # Update controller
        self.controller.update_settings({'stability_threshold': value})

    def update_dwell_time(self):
        """Update dwell time setting"""
        value = self.dwell_slider.value() / 10.0
        self.settings_manager.set('dwell_time', value)

        # Update label
        self.dwell_value_label.setText(f"{value:.1f}s")

        # Update controller
        self.controller.update_settings({'dwell_time': value})

    def update_scroll_sensitivity(self):
        """Update scroll sensitivity setting"""
        value = self.scroll_slider.value()
        self.settings_manager.set('scroll_sensitivity', value)

        # Update label
        self.scroll_value_label.setText(f"{value}")

        # Update controller
        self.controller.update_settings({'scroll_sensitivity': value})

    def update_pinch_threshold(self):
        """Update pinch threshold setting"""
        value = self.pinch_slider.value() / 100.0
        self.settings_manager.set('pinch_threshold', value)

        # Update label
        self.pinch_value_label.setText(f"{value:.2f}")

        # Update controller
        self.controller.update_settings({'pinch_threshold': value})

    def toggle_start_minimized(self):
        """Toggle start minimized setting"""
        value = self.minimized_checkbox.isChecked()
        self.settings_manager.set('start_minimized', value)

    def toggle_start_on_boot(self):
        """Toggle start on boot setting"""
        value = self.autostart_checkbox.isChecked()
        self.settings_manager.set('start_on_boot', value)

        # Configure autostart
        utils.setup_autostart(value)

    def toggle_show_gestures(self):
        """Toggle show gestures setting"""
        value = self.gestures_checkbox.isChecked()
        self.settings_manager.set('show_gestures', value)

        # Update controller
        self.controller.update_settings({'show_gestures': value})

    def change_theme(self, theme_name):
        """Change application theme"""
        self.settings_manager.set('theme', theme_name.lower())
        # Theme changes would require app restart to fully apply
        # We could implement a light theme here if needed

    def reset_settings(self):
        """Reset all settings to defaults"""
        self.settings_manager.reset()

        # Update UI with default values
        self.smoothing_slider.setValue(int(self.settings_manager.get('smoothing_factor', 0.8) * 10))
        self.stability_slider.setValue(self.settings_manager.get('stability_threshold', 5))
        self.dwell_slider.setValue(int(self.settings_manager.get('dwell_time', 0.8) * 10))
        self.scroll_slider.setValue(self.settings_manager.get('scroll_sensitivity', 5))
        self.pinch_slider.setValue(int(self.settings_manager.get('pinch_threshold', 0.1) * 100))
        self.camera_combo.setCurrentIndex(self.settings_manager.get('camera_index', 0))
        self.minimized_checkbox.setChecked(self.settings_manager.get('start_minimized', False))
        self.autostart_checkbox.setChecked(self.settings_manager.get('start_on_boot', False))
        self.gestures_checkbox.setChecked(self.settings_manager.get('show_gestures', True))
        self.theme_combo.setCurrentText(self.settings_manager.get('theme', 'dark').capitalize())

        # Update controller
        self.controller.update_settings(self.settings_manager.current)

    def closeEvent(self, event: QCloseEvent):
        """Handle window close event"""
        # Minimize to tray instead of closing
        event.ignore()
        self.hide()

    def quit_application(self):
        """Quit the application"""
        # Stop video thread
        if self.video_thread.isRunning():
            self.video_thread.stop()

        # Save settings
        self.settings_manager.save()

        # Quit application
        QApplication.quit()


def main():
    # Create application
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # Don't quit when window is closed

    # Set application name and organization
    app.setApplicationName("NoMouse")
    app.setOrganizationName("NoMouse")

    # Create and show main window
    window = NoMouseApp()
    window.show()

    # Run application
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
