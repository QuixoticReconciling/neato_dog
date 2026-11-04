import os #ask what for
import cv2
import mediapipe as mp

from cv_bridge import CvBridge
from sensor_msgs.msg import Image

"""
Hand gesture recognition using MediaPipe and OpenCV.
"""

mp_hands = mp.solutions.hands

def is_open_hand(hand_landmarks):
    """
    Check if the hand is open by checking fingertip landmarks are above lower joints.

    Args:
        hand_landmarks: The hand landmarks detected by MediaPipe.

    Returns:
        True if the hand is open, False otherwise.
    """
    finger_tips = [8, 12, 16, 20] #doesn't include the thumb bc we only want to check height in y
    finger_pips = [6, 10, 14, 18] #lower landmarks so there's more room for error

    for tip, pip in zip(finger_tips, finger_pips):
        if hand_landmarks.landmark[tip].y > hand_landmarks.landmark[pip].y:
            return False
    return True

def is_zero(hand_landmarks):
    """
    Check if the hand is making a zero gesture with a fist

    Args:
        hand_landmarks: The hand landmarks detected by MediaPipe.

    Returns:
        True if the hand is making a zero gesture, False otherwise.
    """
    thumb_tip = 4
    middle_finger_tip = 12

    thumb_tip_y = hand_landmarks.landmark[thumb_tip].y
    middle_finger_tip_y = hand_landmarks.landmark[middle_finger_tip].y

    if abs(thumb_tip_y-middle_finger_tip_y) < 0.03:
        return True
    return False

def is_peace_sign(hand_landmarks):
    """
    Check if the hand is making a peace sign gesture with the index and middle fingers extended.

    Args:
        hand_landmarks: The hand landmarks detected by MediaPipe.

    Returns:
        True if the hand is making a peace sign gesture, False otherwise.
    """
    index_finger_tip = 8
    index_finger_pip = 6
    middle_finger_tip = 12
    middle_finger_pip = 10
    ring_finger_tip = 16
    ring_finger_pip = 14
    pinky_finger_tip = 20
    pinky_finger_pip = 18


    if hand_landmarks.landmark[index_finger_tip].y < hand_landmarks.landmark[index_finger_pip].y and \
       hand_landmarks.landmark[middle_finger_tip].y < hand_landmarks.landmark[middle_finger_pip].y and \
        hand_landmarks.landmark[ring_finger_tip].y > hand_landmarks.landmark[ring_finger_pip].y and \
        hand_landmarks.landmark[pinky_finger_tip].y > hand_landmarks.landmark[pinky_finger_pip].y:
        return True
    return False

def classify_hand_gesture(hand_landmarks):
    """
    Classify the hand gesture based on the detected hand landmarks.

    Args:
        hand_landmarks: The hand landmarks detected by MediaPipe.

    Returns:
        A string representing the classified hand gesture.
    """
    if is_open_hand(hand_landmarks):
        return "Open Hand"
    elif is_zero(hand_landmarks):
        return "Zero"
    elif is_peace_sign(hand_landmarks):
        return "Peace Sign"
    else:
        return "Unknown Gesture"

