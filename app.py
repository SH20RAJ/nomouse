import sys
import os
import cv2
import threading
import time
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                            QHBoxLayout, QPushButton, QLabel, QSlider, QCheckBox,
                            QComboBox, QSystemTrayIcon, QMenu, QTabWidget)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt6.QtGui import QIcon, QImage, QPixmap, QCloseEvent

from controller import HandGestureController
from settings import Settings
import utils

class VideoThread(QThread):
    change_pixmap_signal = pyqtSignal(QImage)

    def __init__(self, camera_index=0):
        super().__init__()
        self.camera_index = camera_index
        self.running = True
        self.controller = None
        self.settings = None

    def set_controller(self, controller):
        self.controller = controller

    def set_settings(self, settings):
        self.settings = settings

    def set_camera_index(self, index):
        self.camera_index = index

    def run(self):
        cap = cv2.VideoCapture(self.camera_index)

        while self.running:
            ret, frame = cap.read()
            if not ret:
                break

            # Flip frame horizontally for natural movement
            frame = cv2.flip(frame, 1)

            if self.controller and self.settings and self.settings.get('enabled'):
                # Process frame and detect hands
                results = self.controller.process_frame(frame)

                # Draw hand landmarks
                self.controller.draw_landmarks(frame, results)

                # Process hand gestures and control mouse
                if results.multi_hand_landmarks:
                    hand_landmarks = results.multi_hand_landmarks[0]
                    gesture_state = self.controller.get_gesture(hand_landmarks)
                    self.controller.control_mouse(hand_landmarks, gesture_state)

            # Convert to Qt format for display
            rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)

            # Emit signal with the image
            self.change_pixmap_signal.emit(qt_image)

            # Sleep to reduce CPU usage
            time.sleep(0.01)

        cap.release()

    def stop(self):
        self.running = False
        self.wait()


class NoMouseApp(QMainWindow):
    def __init__(self):
        super().__init__()

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

        # Start video thread if enabled
        if self.settings_manager.get('enabled'):
            self.video_thread.start()

        # Start minimized if configured
        if self.settings_manager.get('start_minimized'):
            self.hide()

    def init_ui(self):
        # Main window setup
        self.setWindowTitle('NoMouse - Hand Gesture Control')
        self.setGeometry(100, 100, 800, 600)

        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Create tabs
        tabs = QTabWidget()
        main_layout.addWidget(tabs)

        # Main tab
        main_tab = QWidget()
        main_tab_layout = QVBoxLayout(main_tab)

        # Video display
        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setMinimumSize(640, 480)
        main_tab_layout.addWidget(self.video_label)

        # Controls
        controls_layout = QHBoxLayout()

        # Enable/Disable button
        self.toggle_button = QPushButton('Disable' if self.settings_manager.get('enabled') else 'Enable')
        self.toggle_button.clicked.connect(self.toggle_gesture_control)
        controls_layout.addWidget(self.toggle_button)

        main_tab_layout.addLayout(controls_layout)

        # Settings tab
        settings_tab = QWidget()
        settings_layout = QVBoxLayout(settings_tab)

        # Camera selection
        camera_layout = QHBoxLayout()
        camera_layout.addWidget(QLabel('Camera:'))
        self.camera_combo = QComboBox()

        # Add camera options
        for i in range(5):  # Try first 5 camera indices
            self.camera_combo.addItem(f'Camera {i}')

        self.camera_combo.setCurrentIndex(self.settings_manager.get('camera_index', 0))
        self.camera_combo.currentIndexChanged.connect(self.change_camera)
        camera_layout.addWidget(self.camera_combo)
        settings_layout.addLayout(camera_layout)

        # Smoothing settings
        smoothing_layout = QHBoxLayout()
        smoothing_layout.addWidget(QLabel('Slow Movement Smoothing:'))
        self.slow_slider = QSlider(Qt.Orientation.Horizontal)
        self.slow_slider.setRange(1, 10)
        self.slow_slider.setValue(int(self.settings_manager.get('smoothing_slow', 0.5) * 10))
        self.slow_slider.valueChanged.connect(self.update_smoothing)
        smoothing_layout.addWidget(self.slow_slider)
        settings_layout.addLayout(smoothing_layout)

        fast_smoothing_layout = QHBoxLayout()
        fast_smoothing_layout.addWidget(QLabel('Fast Movement Smoothing:'))
        self.fast_slider = QSlider(Qt.Orientation.Horizontal)
        self.fast_slider.setRange(1, 10)
        self.fast_slider.setValue(int(self.settings_manager.get('smoothing_fast', 0.8) * 10))
        self.fast_slider.valueChanged.connect(self.update_smoothing)
        fast_smoothing_layout.addWidget(self.fast_slider)
        settings_layout.addLayout(fast_smoothing_layout)

        # Scroll sensitivity
        scroll_layout = QHBoxLayout()
        scroll_layout.addWidget(QLabel('Scroll Sensitivity:'))
        self.scroll_slider = QSlider(Qt.Orientation.Horizontal)
        self.scroll_slider.setRange(1, 10)
        self.scroll_slider.setValue(self.settings_manager.get('scroll_sensitivity', 5))
        self.scroll_slider.valueChanged.connect(self.update_scroll_sensitivity)
        scroll_layout.addWidget(self.scroll_slider)
        settings_layout.addLayout(scroll_layout)

        # Start minimized option
        self.minimized_checkbox = QCheckBox('Start Minimized')
        self.minimized_checkbox.setChecked(self.settings_manager.get('start_minimized', False))
        self.minimized_checkbox.stateChanged.connect(self.toggle_start_minimized)
        settings_layout.addWidget(self.minimized_checkbox)

        # Start on boot option
        self.autostart_checkbox = QCheckBox('Start on System Boot')
        self.autostart_checkbox.setChecked(self.settings_manager.get('start_on_boot', False))
        self.autostart_checkbox.stateChanged.connect(self.toggle_start_on_boot)
        settings_layout.addWidget(self.autostart_checkbox)

        # Add tabs
        tabs.addTab(main_tab, 'Main')
        tabs.addTab(settings_tab, 'Settings')

        # System tray setup
        self.setup_system_tray()

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
        self.video_label.setPixmap(QPixmap.fromImage(image).scaled(
            self.video_label.width(), self.video_label.height(),
            Qt.AspectRatioMode.KeepAspectRatio))

    def toggle_gesture_control(self):
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

    def change_camera(self, index):
        self.settings_manager.set('camera_index', index)

        # Restart video thread with new camera
        if self.video_thread.isRunning():
            self.video_thread.stop()

        self.video_thread = VideoThread(index)
        self.video_thread.set_controller(self.controller)
        self.video_thread.set_settings(self.settings_manager.current)
        self.video_thread.change_pixmap_signal.connect(self.update_image)

        if self.settings_manager.get('enabled'):
            self.video_thread.start()

    def update_smoothing(self):
        slow_value = self.slow_slider.value() / 10.0
        fast_value = self.fast_slider.value() / 10.0

        self.settings_manager.set('smoothing_slow', slow_value)
        self.settings_manager.set('smoothing_fast', fast_value)

        # Update controller
        self.controller.update_settings({
            'smoothing_slow': slow_value,
            'smoothing_fast': fast_value
        })

    def update_scroll_sensitivity(self):
        value = self.scroll_slider.value()
        self.settings_manager.set('scroll_sensitivity', value)

        # Update controller
        self.controller.update_settings({'scroll_sensitivity': value})

    def toggle_start_minimized(self):
        value = self.minimized_checkbox.isChecked()
        self.settings_manager.set('start_minimized', value)

    def toggle_start_on_boot(self):
        value = self.autostart_checkbox.isChecked()
        self.settings_manager.set('start_on_boot', value)

        # Configure autostart
        utils.setup_autostart(value)

    def closeEvent(self, event: QCloseEvent):
        # Minimize to tray instead of closing
        event.ignore()
        self.hide()

    def quit_application(self):
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

    # Create and show main window
    window = NoMouseApp()
    window.show()

    # Run application
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
