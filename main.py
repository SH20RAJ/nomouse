import cv2
import mediapipe as mp
import pyautogui
import numpy as np

class HandGestureController:
    def __init__(self):
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

    def get_gesture(self, hand_landmarks):
        # Extract finger states
        thumb_tip = hand_landmarks.landmark[4].y
        thumb_ip = hand_landmarks.landmark[3].y
        index_tip = hand_landmarks.landmark[8].y
        index_pip = hand_landmarks.landmark[6].y
        middle_tip = hand_landmarks.landmark[12].y
        middle_pip = hand_landmarks.landmark[10].y

        # Detect gestures
        thumb_up = thumb_tip < thumb_ip
        index_up = index_tip < index_pip
        middle_up = middle_tip < middle_pip

        # Return gesture state
        return {
            'thumb_up': thumb_up,
            'index_up': index_up,
            'middle_up': middle_up
        }

    def control_mouse(self, hand_landmarks, gesture_state):
        # Get hand position
        index_tip = hand_landmarks.landmark[8]
        x = int(index_tip.x * self.screen_width)
        y = int(index_tip.y * self.screen_height)

        # Smooth mouse movement
        smoothing = 0.5 if gesture_state['thumb_up'] else 0.8
        x = int(self.prev_x + (x - self.prev_x) * smoothing)
        y = int(self.prev_y + (y - self.prev_y) * smoothing)

        # Move mouse cursor
        pyautogui.moveTo(x, y)
        self.prev_x, self.prev_y = x, y

        # Handle clicks
        if gesture_state['index_up']:
            pyautogui.click(button='left')
        elif gesture_state['middle_up']:
            pyautogui.click(button='right')

def main():
    controller = HandGestureController()
    cap = cv2.VideoCapture(0)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Flip frame horizontally for natural movement
        frame = cv2.flip(frame, 1)

        # Process frame and detect hands
        results = controller.process_frame(frame)

        # Draw hand landmarks
        controller.draw_landmarks(frame, results)

        # Process hand gestures and control mouse
        if results.multi_hand_landmarks:
            hand_landmarks = results.multi_hand_landmarks[0]
            gesture_state = controller.get_gesture(hand_landmarks)
            controller.control_mouse(hand_landmarks, gesture_state)

        # Display frame
        cv2.imshow('NoMouse - Hand Gesture Control', frame)

        # Break loop on 'q' press
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    main()