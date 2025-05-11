import cv2
import mediapipe as mp
import pyautogui
import numpy as np
import time

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
        self.screen_width, self.screen_height = pyautogui.size()
        self.prev_x, self.prev_y = 0, 0
        pyautogui.FAILSAFE = False
        
        # Default settings
        self.settings = settings or {
            'smoothing_slow': 0.5,
            'smoothing_fast': 0.8,
            'scroll_sensitivity': 5,
            'enabled': True
        }
        
        # For scroll gesture detection
        self.prev_hand_y = 0
        self.scroll_cooldown = 0
        
        # For gesture visualization
        self.last_gesture = None
        self.gesture_time = 0

    def process_frame(self, frame):
        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # Process the frame and detect hands
        results = self.hands.process(rgb_frame)
        return results

    def draw_landmarks(self, frame, results):
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                self.mp_draw.draw_landmarks(
                    frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
                
                # Add gesture visualization
                if self.last_gesture and time.time() - self.gesture_time < 1.0:
                    gesture_text = f"Gesture: {self.last_gesture}"
                    cv2.putText(frame, gesture_text, (10, 30), 
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    def get_gesture(self, hand_landmarks):
        # Extract finger states
        thumb_tip = hand_landmarks.landmark[4].y
        thumb_ip = hand_landmarks.landmark[3].y
        index_tip = hand_landmarks.landmark[8].y
        index_pip = hand_landmarks.landmark[6].y
        middle_tip = hand_landmarks.landmark[12].y
        middle_pip = hand_landmarks.landmark[10].y
        ring_tip = hand_landmarks.landmark[16].y
        ring_pip = hand_landmarks.landmark[14].y
        pinky_tip = hand_landmarks.landmark[20].y
        pinky_pip = hand_landmarks.landmark[18].y

        # Detect gestures
        thumb_up = thumb_tip < thumb_ip
        index_up = index_tip < index_pip
        middle_up = middle_tip < middle_pip
        ring_up = ring_tip < ring_pip
        pinky_up = pinky_tip < pinky_pip
        
        # Detect scroll gesture (all fingers up)
        scroll_gesture = index_up and middle_up and ring_up and pinky_up
        
        # Return gesture state
        return {
            'thumb_up': thumb_up,
            'index_up': index_up,
            'middle_up': middle_up,
            'ring_up': ring_up,
            'pinky_up': pinky_up,
            'scroll_gesture': scroll_gesture
        }

    def control_mouse(self, hand_landmarks, gesture_state):
        if not self.settings.get('enabled', True):
            return
            
        # Get hand position
        index_tip = hand_landmarks.landmark[8]
        x = int(index_tip.x * self.screen_width)
        y = int(index_tip.y * self.screen_height)

        # Smooth mouse movement
        smoothing = self.settings.get('smoothing_slow', 0.5) if gesture_state['thumb_up'] else self.settings.get('smoothing_fast', 0.8)
        x = int(self.prev_x + (x - self.prev_x) * smoothing)
        y = int(self.prev_y + (y - self.prev_y) * smoothing)

        # Move mouse cursor
        pyautogui.moveTo(x, y)
        self.prev_x, self.prev_y = x, y

        # Handle clicks
        if gesture_state['index_up'] and not gesture_state['middle_up'] and not gesture_state['ring_up'] and not gesture_state['pinky_up']:
            pyautogui.click(button='left')
            self.last_gesture = "Left Click"
            self.gesture_time = time.time()
        elif gesture_state['middle_up'] and not gesture_state['index_up'] and not gesture_state['ring_up'] and not gesture_state['pinky_up']:
            pyautogui.click(button='right')
            self.last_gesture = "Right Click"
            self.gesture_time = time.time()
            
        # Handle scrolling
        if gesture_state['scroll_gesture']:
            # Get hand y position for scrolling
            hand_y = hand_landmarks.landmark[0].y
            
            # Calculate scroll direction and amount
            if time.time() > self.scroll_cooldown:
                y_diff = hand_y - self.prev_hand_y
                if abs(y_diff) > 0.01:  # Threshold to avoid accidental scrolls
                    scroll_amount = int(y_diff * self.settings.get('scroll_sensitivity', 5) * 10)
                    pyautogui.scroll(scroll_amount)
                    self.scroll_cooldown = time.time() + 0.1  # Cooldown to prevent too rapid scrolling
                    
                    if scroll_amount > 0:
                        self.last_gesture = "Scroll Up"
                    else:
                        self.last_gesture = "Scroll Down"
                    self.gesture_time = time.time()
            
            self.prev_hand_y = hand_y

    def update_settings(self, settings):
        """Update controller settings"""
        self.settings.update(settings)
