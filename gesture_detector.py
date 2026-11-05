import os
import time
import cv2
import rclpy
import mediapipe as mp
from cv_bridge import CvBridge
from sensor_msgs.msg import Image
from rclpy.node import Node
from std_msgs.msg import String
from threading import Thread

from neato_dog.hand_gestures import classify_hand_gesture

os.environ['QT_QPA_FONTDIR'] = '/usr/share/fonts/truetype/dejavu'

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

class GestureDetector(Node):
    """Subscribes to the camera, detects hand gestures, and publishes them."""
 
    def __init__(self, image_topic):
        super().__init__('gesture_detector')
        self.cv_image = None #latest image from the camera
        self.bridge = CvBridge() #used to convert ROS messages to OpenCV 
 
        self.create_subscription(Image, image_topic, self.process_image, 10)
        self.gesture_pub = self.create_publisher(String, 'gesture', 10)
 
        self.hands = mp_hands.Hands(max_num_hands=1,
                                    min_detection_confidence=0.6,
                                    min_tracking_confidence=0.5)
 
        thread = Thread(target=self.loop_wrapper, daemon=True)
        thread.start()
 
    def process_image(self, msg):
        """Stash the latest camera image as an OpenCV (BGR) image."""
        self.cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")
 
    def loop_wrapper(self):
        """Runs the processing loop in its own thread"""
        cv2.namedWindow('gesture_window')
        while True:
            self.run_loop()
            time.sleep(0.05)
 
    def run_loop(self):
        """Detect a gesture in the latest image and publish"""
        if self.cv_image is None:
            return
 
        frame = self.cv_image.copy()
        results = self.hands.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        gesture = "none"

        if results.multi_hand_landmarks:
            hand = results.multi_hand_landmarks[0]
            mp_drawing.draw_landmarks(frame, hand, mp_hands.HAND_CONNECTIONS)
            gesture = classify_hand_gesture(hand)
 
        self.gesture_pub.publish(String(data=gesture))
 
        color = (0, 200, 0) if gesture != "none" else (0, 0, 255)
        cv2.putText(frame, gesture, (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.1, color, 3)
        cv2.imshow('gesture_window', frame)
        cv2.waitKey(5)
 
 
def main(args=None):
    rclpy.init(args=args)
    node = GestureDetector("camera/image_raw")
    rclpy.spin(node)
    rclpy.shutdown()
 
 
if __name__ == '__main__':
    main()
