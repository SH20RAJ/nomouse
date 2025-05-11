import cv2
import mediapipe as mp
import pyautogui
import numpy as np
import time
import math
from collections import deque

class KalmanFilter:
    """
    A simple Kalman filter for smoothing cursor movement
    """
    def __init__(self, process_variance=0.001, measurement_variance=0.1):
        self.process_variance = process_variance
        self.measurement_variance = measurement_variance
        self.posteri_estimate = np.array([0.0, 0.0])
        self.posteri_error_estimate = np.array([1.0, 1.0])

    def update(self, measurement):
        # Prediction update
        priori_estimate = self.posteri_estimate
        priori_error_estimate = self.posteri_error_estimate + self.process_variance

        # Measurement update
        blending_factor = priori_error_estimate / (priori_error_estimate + self.measurement_variance)
        self.posteri_estimate = priori_estimate + blending_factor * (measurement - priori_estimate)
        self.posteri_error_estimate = (1 - blending_factor) * priori_error_estimate

        return self.posteri_estimate

class HandGestureController:
    def __init__(self, settings=None):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7
        )
        self.mp_draw = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles

        # Screen dimensions
        self.screen_width, self.screen_height = pyautogui.size()
        self.prev_x, self.prev_y = self.screen_width // 2, self.screen_height // 2
        pyautogui.FAILSAFE = False

        # Default settings
        self.settings = settings or {
            'smoothing_factor': 0.8,      # Higher = smoother but more lag
            'stability_threshold': 5,     # Pixels of movement to ignore (reduces jitter)
            'dwell_time': 0.8,            # Seconds to hold for a click
            'scroll_sensitivity': 5,      # Scroll speed
            'enabled': True,
            'pinch_threshold': 0.1        # Distance threshold for pinch detection
        }

        # Advanced cursor control
        self.kalman_filter = KalmanFilter()
        self.position_history = deque(maxlen=10)  # Store recent positions for trend analysis
        for _ in range(10):
            self.position_history.append((self.prev_x, self.prev_y))

        # Gesture state tracking
        self.hover_start_time = 0
        self.hover_position = None
        self.is_hovering = False
        self.prev_hand_y = 0
        self.scroll_cooldown = 0
        self.pinch_active = False
        self.pinch_start_time = 0

        # For gesture visualization
        self.last_gesture = None
        self.gesture_time = 0
        self.gesture_color = (0, 255, 0)  # Default green

        # Finger tracking
        self.index_finger_tip = None
        self.middle_finger_tip = None
        self.thumb_tip = None
        self.index_finger_history = deque(maxlen=15)  # For smoother tracking

    def process_frame(self, frame):
        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # Process the frame and detect hands
        results = self.hands.process(rgb_frame)
        return results

    def draw_landmarks(self, frame, results):
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # Draw hand landmarks with custom style
                self.mp_draw.draw_landmarks(
                    frame,
                    hand_landmarks,
                    self.mp_hands.HAND_CONNECTIONS,
                    self.mp_drawing_styles.get_default_hand_landmarks_style(),
                    self.mp_drawing_styles.get_default_hand_connections_style())

                # Get frame dimensions
                frame_height, frame_width = frame.shape[:2]

                # Draw cursor position indicator
                if self.index_finger_tip:
                    x, y = int(self.index_finger_tip[0] * frame_width), int(self.index_finger_tip[1] * frame_height)

                    # Draw cursor with glow effect
                    # Outer glow
                    cv2.circle(frame, (x, y), 14, (255, 255, 255, 150), -1)  # White glow
                    # Inner circle
                    cv2.circle(frame, (x, y), 10, (0, 165, 255), -1)  # Orange circle
                    # White outline
                    cv2.circle(frame, (x, y), 12, (255, 255, 255), 2)

                # Draw hover indicator if hovering
                if self.is_hovering and self.hover_position:
                    hover_x, hover_y = int(self.hover_position[0] * frame_width), int(self.hover_position[1] * frame_height)
                    # Calculate progress for hover animation
                    hover_progress = min(1.0, (time.time() - self.hover_start_time) / self.settings.get('dwell_time', 0.8))
                    radius = 18
                    thickness = 3

                    # Draw progress circle with shadow
                    cv2.circle(frame, (hover_x, hover_y), radius+2, (0, 0, 0, 100), thickness)  # Shadow
                    cv2.circle(frame, (hover_x, hover_y), radius, (255, 255, 255), thickness)  # White circle

                    # Draw progress arc
                    start_angle = -90  # Start from top
                    end_angle = start_angle + (360 * hover_progress)
                    cv2.ellipse(frame, (hover_x, hover_y), (radius, radius),
                                0, start_angle, end_angle, (0, 255, 0), thickness+1)

                    # Add click text when almost complete
                    if hover_progress > 0.7:
                        click_text = "CLICK"
                        text_size = cv2.getTextSize(click_text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]
                        text_x = hover_x - text_size[0] // 2
                        text_y = hover_y + radius + 20

                        # Draw text with shadow
                        cv2.putText(frame, click_text, (text_x+1, text_y+1),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)  # Shadow
                        cv2.putText(frame, click_text, (text_x, text_y),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

                # Draw pinch visualization
                if hasattr(self, 'pinch_active') and self.pinch_active and self.thumb_tip and self.index_finger_tip:
                    thumb_x, thumb_y = int(self.thumb_tip[0] * frame_width), int(self.thumb_tip[1] * frame_height)
                    index_x, index_y = int(self.index_finger_tip[0] * frame_width), int(self.index_finger_tip[1] * frame_height)

                    # Draw line between thumb and index
                    cv2.line(frame, (thumb_x, thumb_y), (index_x, index_y), (0, 165, 255), 2)

                    # Draw pinch progress
                    if hasattr(self, 'pinch_start_time'):
                        pinch_progress = min(1.0, (time.time() - self.pinch_start_time) / 0.3)
                        mid_x, mid_y = (thumb_x + index_x) // 2, (thumb_y + index_y) // 2

                        # Draw progress circle
                        radius = 10
                        cv2.circle(frame, (mid_x, mid_y), radius, (255, 255, 255), 2)
                        cv2.circle(frame, (mid_x, mid_y), int(radius * pinch_progress), (0, 165, 255), -1)

                # Draw drag visualization
                if hasattr(self, 'drag_active') and self.drag_active:
                    # Draw drag indicator
                    drag_text = "DRAGGING"
                    text_size = cv2.getTextSize(drag_text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
                    text_x = frame_width - text_size[0] - 20
                    text_y = 80

                    # Draw background
                    cv2.rectangle(frame,
                                 (text_x - 10, text_y - 25),
                                 (text_x + text_size[0] + 10, text_y + 5),
                                 (0, 0, 0, 150), -1)

                    # Draw text
                    cv2.putText(frame, drag_text, (text_x, text_y),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)

                # Add gesture visualization
                if self.last_gesture and time.time() - self.gesture_time < 1.5:
                    gesture_text = f"{self.last_gesture}"
                    text_size = cv2.getTextSize(gesture_text, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)[0]
                    text_x = frame_width - text_size[0] - 20
                    text_y = 40

                    # Draw background with rounded corners
                    cv2.rectangle(frame,
                                 (text_x - 10, text_y - 30),
                                 (text_x + text_size[0] + 10, text_y + 10),
                                 (0, 0, 0, 180), -1)

                    # Draw text with shadow for better visibility
                    cv2.putText(frame, gesture_text, (text_x+1, text_y+1),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)  # Shadow
                    cv2.putText(frame, gesture_text, (text_x, text_y),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.8, self.gesture_color, 2)

                # Add gesture guide in the bottom left based on CONTROL.md
                if self.settings.get('show_gestures', True):
                    guide_x, guide_y = 20, frame_height - 20
                    cv2.putText(frame, "👆 Point: Move cursor", (guide_x, guide_y - 120),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                    cv2.putText(frame, "👌 Index+Thumb: Left-click", (guide_x, guide_y - 90),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                    cv2.putText(frame, "👌 Middle+Thumb: Right-click", (guide_x, guide_y - 60),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                    cv2.putText(frame, "✌️ Two fingers: Scroll", (guide_x, guide_y - 30),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                    cv2.putText(frame, "✊ Pinch & hold: Drag", (guide_x, guide_y),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    def get_gesture(self, hand_landmarks):
        """Detect hand gestures and track finger positions based on CONTROL.md recommendations"""
        # Store all finger positions and joints
        self.wrist = (hand_landmarks.landmark[0].x, hand_landmarks.landmark[0].y)

        # Thumb landmarks
        self.thumb_cmc = (hand_landmarks.landmark[1].x, hand_landmarks.landmark[1].y)
        self.thumb_mcp = (hand_landmarks.landmark[2].x, hand_landmarks.landmark[2].y)
        self.thumb_ip = (hand_landmarks.landmark[3].x, hand_landmarks.landmark[3].y)
        self.thumb_tip = (hand_landmarks.landmark[4].x, hand_landmarks.landmark[4].y)

        # Index finger landmarks
        self.index_mcp = (hand_landmarks.landmark[5].x, hand_landmarks.landmark[5].y)
        self.index_pip = (hand_landmarks.landmark[6].x, hand_landmarks.landmark[6].y)
        self.index_dip = (hand_landmarks.landmark[7].x, hand_landmarks.landmark[7].y)
        self.index_finger_tip = (hand_landmarks.landmark[8].x, hand_landmarks.landmark[8].y)

        # Middle finger landmarks
        self.middle_mcp = (hand_landmarks.landmark[9].x, hand_landmarks.landmark[9].y)
        self.middle_pip = (hand_landmarks.landmark[10].x, hand_landmarks.landmark[10].y)
        self.middle_dip = (hand_landmarks.landmark[11].x, hand_landmarks.landmark[11].y)
        self.middle_finger_tip = (hand_landmarks.landmark[12].x, hand_landmarks.landmark[12].y)

        # Ring finger landmarks
        self.ring_mcp = (hand_landmarks.landmark[13].x, hand_landmarks.landmark[13].y)
        self.ring_pip = (hand_landmarks.landmark[14].x, hand_landmarks.landmark[14].y)
        self.ring_dip = (hand_landmarks.landmark[15].x, hand_landmarks.landmark[15].y)
        self.ring_finger_tip = (hand_landmarks.landmark[16].x, hand_landmarks.landmark[16].y)

        # Pinky finger landmarks
        self.pinky_mcp = (hand_landmarks.landmark[17].x, hand_landmarks.landmark[17].y)
        self.pinky_pip = (hand_landmarks.landmark[18].x, hand_landmarks.landmark[18].y)
        self.pinky_dip = (hand_landmarks.landmark[19].x, hand_landmarks.landmark[19].y)
        self.pinky_finger_tip = (hand_landmarks.landmark[20].x, hand_landmarks.landmark[20].y)

        # Add index finger position to history for smoothing
        self.index_finger_history.append(self.index_finger_tip)

        # Calculate average position from history (smoothing)
        avg_x = sum(p[0] for p in self.index_finger_history) / len(self.index_finger_history)
        avg_y = sum(p[1] for p in self.index_finger_history) / len(self.index_finger_history)
        smooth_index_tip = (avg_x, avg_y)

        # Calculate hand orientation and pose
        hand_direction_x = self.index_mcp[0] - self.wrist[0]
        hand_direction_y = self.index_mcp[1] - self.wrist[1]
        hand_facing_camera = hand_direction_y < 0  # Hand is facing camera if index MCP is above wrist

        # Detect finger states (extended or not)
        # A finger is extended if its tip is significantly above its PIP joint
        extension_threshold = 0.05  # Threshold for determining if a finger is extended

        thumb_extended = self.thumb_tip[1] < self.thumb_ip[1] - extension_threshold
        index_extended = self.index_finger_tip[1] < self.index_pip[1] - extension_threshold
        middle_extended = self.middle_finger_tip[1] < self.middle_pip[1] - extension_threshold
        ring_extended = self.ring_finger_tip[1] < self.ring_pip[1] - extension_threshold
        pinky_extended = self.pinky_finger_tip[1] < self.pinky_pip[1] - extension_threshold

        # Count extended fingers
        extended_fingers = sum([thumb_extended, index_extended, middle_extended, ring_extended, pinky_extended])

        # === GESTURE DETECTION BASED ON CONTROL.md ===

        # 1. CURSOR MOVEMENT: Point with index finger (hand relaxed)
        # "A natural way to move the cursor is by pointing with the index finger"
        pointing_gesture = index_extended and not middle_extended and not ring_extended and not pinky_extended

        # 2. LEFT CLICK: Pinch index+thumb together (tap)
        # "Left click: A pinch or tap gesture. For example, touching the tips of thumb and index finger together"
        index_thumb_distance = self.calculate_distance(self.thumb_tip, self.index_finger_tip)
        pinch_threshold = self.settings.get('pinch_threshold', 0.1)
        index_thumb_pinch = index_thumb_distance < pinch_threshold

        # 3. RIGHT CLICK: Pinch middle+thumb together
        # "Right click: Another pinch combination... HandMouse uses thumb+middle pinch"
        middle_thumb_distance = self.calculate_distance(self.thumb_tip, self.middle_finger_tip)
        middle_thumb_pinch = middle_thumb_distance < pinch_threshold

        # 4. DRAG & DROP: Pinch-and-hold + move
        # "Drag & Drop: 'Click-and-hold' with pinch. Users pinch (index+thumb) and hold while moving"
        drag_gesture = index_thumb_pinch and pointing_gesture

        # 5. SCROLLING: Two-finger swipe (index+middle extended)
        # "Scrolling: A swipe or pinch-scroll gesture... raising two fingers (index+middle) like a 'two-finger swipe'"
        two_finger_gesture = index_extended and middle_extended and not ring_extended and not pinky_extended

        # Calculate angle between index and middle finger for V shape detection
        finger_angle = self.calculate_angle(self.index_finger_tip, self.middle_mcp, self.middle_finger_tip)
        v_shape = two_finger_gesture and finger_angle > 15  # V shape with significant angle

        # 6. DOUBLE CLICK: Quick double pinch or raise index+middle
        # "Double Click: Quick double pinch or raise index+middle"
        double_click_gesture = index_extended and middle_extended and not ring_extended and not pinky_extended and finger_angle < 15

        # 7. ZOOM: Pinch together / spread apart
        # "Zoom: A classic pinch/spread gesture. Bringing thumb and index together"
        # (This would require tracking pinch distance changes over time)

        # 8. OPEN HAND: All fingers extended
        open_hand = thumb_extended and index_extended and middle_extended and ring_extended and pinky_extended

        # Return comprehensive gesture state
        return {
            'smooth_index_tip': smooth_index_tip,
            'pointing_gesture': pointing_gesture,
            'index_thumb_pinch': index_thumb_pinch,  # Left click
            'middle_thumb_pinch': middle_thumb_pinch,  # Right click
            'drag_gesture': drag_gesture,  # Drag and drop
            'two_finger_gesture': two_finger_gesture,  # General two-finger gesture
            'v_shape': v_shape,  # V shape for scrolling
            'double_click_gesture': double_click_gesture,  # Double click
            'open_hand': open_hand,  # Open hand gesture
            'extended_fingers': extended_fingers,
            'hand_facing_camera': hand_facing_camera
        }

    def calculate_angle(self, point1, point2, point3):
        """Calculate angle between three points in degrees"""
        # Convert points to numpy arrays for vector calculations
        p1 = np.array([point1[0], point1[1]])
        p2 = np.array([point2[0], point2[1]])
        p3 = np.array([point3[0], point3[1]])

        # Calculate vectors
        v1 = p1 - p2
        v2 = p3 - p2

        # Calculate angle using dot product
        dot_product = np.dot(v1, v2)
        norm_v1 = np.linalg.norm(v1)
        norm_v2 = np.linalg.norm(v2)

        # Avoid division by zero
        if norm_v1 == 0 or norm_v2 == 0:
            return 0

        cos_angle = dot_product / (norm_v1 * norm_v2)
        # Clamp to avoid numerical errors
        cos_angle = max(min(cos_angle, 1.0), -1.0)
        angle_rad = np.arccos(cos_angle)

        # Convert to degrees
        angle_deg = np.degrees(angle_rad)

        return angle_deg

    def calculate_distance(self, point1, point2):
        """Calculate normalized distance between two points"""
        return math.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)

    def control_mouse(self, hand_landmarks, gesture_state):
        """Control mouse based on detected gestures from CONTROL.md recommendations"""
        if not self.settings.get('enabled', True):
            return

        # Only process if hand is facing the camera
        if not gesture_state.get('hand_facing_camera', True):
            return

        # 1. CURSOR MOVEMENT: Point with index finger (hand relaxed)
        # "A natural way to move the cursor is by pointing with the index finger"
        if gesture_state.get('pointing_gesture', False) or gesture_state.get('two_finger_gesture', False):
            # Get smoothed index finger tip position
            smooth_tip = gesture_state['smooth_index_tip']
            raw_x = int(smooth_tip[0] * self.screen_width)
            raw_y = int(smooth_tip[1] * self.screen_height)

            # Apply Kalman filter for smoother movement (recommended in CONTROL.md)
            # "MediaPipe hand landmarks can fluctuate, so smoothing is essential. Common techniques include low-pass filters and Kalman filters."
            filtered_pos = self.kalman_filter.update(np.array([raw_x, raw_y]))
            x, y = int(filtered_pos[0]), int(filtered_pos[1])

            # Apply stability threshold to reduce jitter
            # "It also helps to ignore tiny hand tremors by thresholding movement"
            stability_threshold = self.settings.get('stability_threshold', 5)
            if abs(x - self.prev_x) < stability_threshold and abs(y - self.prev_y) < stability_threshold:
                x, y = self.prev_x, self.prev_y

            # Apply additional smoothing based on movement speed
            # "Combining a Kalman filter with a small deadzone (ignore sub-pixel jitter) usually works well."
            distance = math.sqrt((x - self.prev_x)**2 + (y - self.prev_y)**2)

            # Adaptive smoothing - more smoothing for small movements, less for large movements
            if distance < 50:  # Small movement
                smoothing_factor = self.settings.get('smoothing_factor', 0.8)
            else:  # Large movement
                smoothing_factor = max(0.3, self.settings.get('smoothing_factor', 0.8) - 0.3)

            x = int(self.prev_x + (x - self.prev_x) * (1 - smoothing_factor))
            y = int(self.prev_y + (y - self.prev_y) * (1 - smoothing_factor))

            # Move mouse cursor
            pyautogui.moveTo(x, y)

            # Store position history
            self.position_history.append((x, y))
            self.prev_x, self.prev_y = x, y

        # 2. LEFT CLICK: Pinch index+thumb together (tap)
        # "Left click: A pinch or tap gesture. For example, touching the tips of thumb and index finger together"
        if gesture_state.get('index_thumb_pinch', False) and not hasattr(self, 'index_thumb_pinch_active'):
            # Start pinch timer
            self.index_thumb_pinch_active = True
            self.index_thumb_pinch_start_time = time.time()
            self.last_gesture = "Left Click Started"
            self.gesture_color = (0, 255, 0)  # Green
            self.gesture_time = time.time()
        elif gesture_state.get('index_thumb_pinch', False) and hasattr(self, 'index_thumb_pinch_active') and self.index_thumb_pinch_active:
            # Pinch is still active, check if we should perform click
            if time.time() - self.index_thumb_pinch_start_time > 0.2 and not hasattr(self, 'left_click_performed'):
                # Perform click after short delay
                pyautogui.click(button='left')
                self.left_click_performed = True
                self.last_gesture = "Left Click"
                self.gesture_color = (0, 255, 0)  # Green
                self.gesture_time = time.time()
        elif not gesture_state.get('index_thumb_pinch', False) and hasattr(self, 'index_thumb_pinch_active'):
            # Reset pinch state
            self.index_thumb_pinch_active = False
            if hasattr(self, 'left_click_performed'):
                delattr(self, 'left_click_performed')

        # 3. RIGHT CLICK: Pinch middle+thumb together
        # "Right click: Another pinch combination... HandMouse uses thumb+middle pinch"
        if gesture_state.get('middle_thumb_pinch', False) and not hasattr(self, 'middle_thumb_pinch_active'):
            # Start pinch timer
            self.middle_thumb_pinch_active = True
            self.middle_thumb_pinch_start_time = time.time()
            self.last_gesture = "Right Click Started"
            self.gesture_color = (0, 165, 255)  # Orange
            self.gesture_time = time.time()
        elif gesture_state.get('middle_thumb_pinch', False) and hasattr(self, 'middle_thumb_pinch_active') and self.middle_thumb_pinch_active:
            # Pinch is still active, check if we should perform click
            if time.time() - self.middle_thumb_pinch_start_time > 0.2 and not hasattr(self, 'right_click_performed'):
                # Perform click after short delay
                pyautogui.click(button='right')
                self.right_click_performed = True
                self.last_gesture = "Right Click"
                self.gesture_color = (0, 165, 255)  # Orange
                self.gesture_time = time.time()
        elif not gesture_state.get('middle_thumb_pinch', False) and hasattr(self, 'middle_thumb_pinch_active'):
            # Reset pinch state
            self.middle_thumb_pinch_active = False
            if hasattr(self, 'right_click_performed'):
                delattr(self, 'right_click_performed')

        # 4. DRAG & DROP: Pinch-and-hold + move
        # "Drag & Drop: 'Click-and-hold' with pinch. Users pinch (index+thumb) and hold while moving"
        if gesture_state.get('drag_gesture', False):
            if not hasattr(self, 'drag_active') or not self.drag_active:
                # Start drag operation
                pyautogui.mouseDown()
                self.drag_active = True
                self.last_gesture = "Drag Start"
                self.gesture_color = (255, 0, 0)  # Red
                self.gesture_time = time.time()
        elif hasattr(self, 'drag_active') and self.drag_active and not gesture_state.get('index_thumb_pinch', False):
            # End drag operation when pinch is released
            pyautogui.mouseUp()
            self.drag_active = False
            self.last_gesture = "Drag End"
            self.gesture_color = (0, 255, 0)  # Green
            self.gesture_time = time.time()

        # 5. SCROLLING: Two-finger swipe (index+middle extended)
        # "Scrolling: A swipe or pinch-scroll gesture... raising two fingers (index+middle) like a 'two-finger swipe'"
        if gesture_state.get('v_shape', False):
            # Calculate vertical movement for scrolling
            current_y = self.wrist[1]

            if time.time() > self.scroll_cooldown:
                y_diff = current_y - self.prev_hand_y
                if abs(y_diff) > 0.01:  # Threshold to avoid accidental scrolls
                    # Invert scroll direction for more natural feel
                    scroll_amount = -int(y_diff * self.settings.get('scroll_sensitivity', 5) * 10)
                    pyautogui.scroll(scroll_amount)
                    self.scroll_cooldown = time.time() + 0.05  # Reduced cooldown for smoother scrolling

                    if abs(scroll_amount) > 0:
                        self.last_gesture = "Scrolling" + (" Down" if scroll_amount > 0 else " Up")
                        self.gesture_color = (255, 165, 0)  # Orange
                        self.gesture_time = time.time()

            self.prev_hand_y = current_y

        # 6. DOUBLE CLICK: Quick double pinch or raise index+middle
        # "Double Click: Quick double pinch or raise index+middle"
        if gesture_state.get('double_click_gesture', False) and not hasattr(self, 'double_click_active'):
            self.double_click_active = True
            self.double_click_start_time = time.time()
        elif gesture_state.get('double_click_gesture', False) and hasattr(self, 'double_click_active'):
            if time.time() - self.double_click_start_time > 0.3 and not hasattr(self, 'double_click_performed'):
                # Perform double click
                pyautogui.doubleClick()
                self.double_click_performed = True
                self.last_gesture = "Double Click"
                self.gesture_color = (0, 255, 255)  # Cyan
                self.gesture_time = time.time()
        elif not gesture_state.get('double_click_gesture', False) and hasattr(self, 'double_click_active'):
            # Reset double click state
            self.double_click_active = False
            if hasattr(self, 'double_click_performed'):
                delattr(self, 'double_click_performed')

    def is_stable_position(self, threshold):
        """Check if the cursor position is stable (not moving much)"""
        if len(self.position_history) < 5:
            return False

        recent_positions = list(self.position_history)[-5:]
        max_x_diff = max(abs(p[0] - q[0]) for p, q in zip(recent_positions, recent_positions[1:]))
        max_y_diff = max(abs(p[1] - q[1]) for p, q in zip(recent_positions, recent_positions[1:]))

        return max_x_diff < threshold and max_y_diff < threshold

    def update_settings(self, settings):
        """Update controller settings"""
        self.settings.update(settings)
