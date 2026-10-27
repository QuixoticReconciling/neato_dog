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
    finger_dips = [6, 10, 14, 18] #lower landmarks so there's more room for error

    for tip, dip in zip(finger_tips, finger_dips):
        if hand_landmarks.landmark[tip].y > hand_landmarks.landmark[dip].y:
            return False
    return True

def is_zero(hand_landmarks):
    """
    Check if the hand is making a zero gesture with the thumb and middle finger touching.

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
    index_finger_dip = 6
    middle_finger_tip = 12
    middle_finger_dip = 10

    if hand_landmarks.landmark[index_finger_tip].y < hand_landmarks.landmark[index_finger_dip].y and \
       hand_landmarks.landmark[middle_finger_tip].y < hand_landmarks.landmark[middle_finger_dip].y:
        return True
    return False