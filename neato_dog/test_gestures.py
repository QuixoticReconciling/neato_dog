"""
Uses the MediaPipe library to detect hand gestures from a webcam feed
"""
import cv2
import mediapipe as mp
from hand_gestures import classify_hand_gesture

hands = mp.solutions.hands.Hands(max_num_hands=1)
draw = mp.solutions.drawing_utils
cam = cv2.VideoCapture(0)

while True:
    ret, frame = cam.read()
    if not ret:
        break
    results = hands.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    label = "no hand"
    if results.multi_hand_landmarks:
        hand = results.multi_hand_landmarks[0]
        draw.draw_landmarks(frame, hand, mp.solutions.hands.HAND_CONNECTIONS)
        label = classify_hand_gesture(hand)
    cv2.putText(frame, label, (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    cv2.imshow("Gestures", frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cam.release()
cv2.destroyAllWindows()