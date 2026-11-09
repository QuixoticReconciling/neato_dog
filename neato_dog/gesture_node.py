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
from rclpy.executors import MultiThreadedExecutor

from neato_dog import hand_gestures
from neato_dog.YOLO_fetch import Fetch
from neato_dog.sit import sitNode
from neato_dog.spin import SpinNode
os.environ['QT_QPA_FONTDIR'] = '/usr/share/fonts/truetype/dejavu'

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

class GestureDetector(Node):
    """Subscribes to the camera, detects hand gestures, and publishes them."""
 
    def __init__(self, image_topic):
        super().__init__('gesture_detector')
        self.cv_image = None #latest image from the camera
        self.bridge = CvBridge() #used to convert ROS messages to OpenCV 

        self.sit = sitNode()
        self.spin = SpinNode()
        self.fetch = Fetch()

 
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
        self.fetch.cv_image = self.cv_image
 
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
            gesture = hand_gestures.classify_hand_gesture(hand)
 
        self.controller(gesture)
 
        color = (0, 200, 0) if gesture != "none" else (0, 0, 255)
        cv2.putText(frame, gesture, (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.1, color, 3)
        cv2.imshow('gesture_window', frame)
        fetch_frame = self.fetch.final #access frame from behavior node to draw annoted boxes
        if self.fetch.state_active and fetch_frame is not None:
            cv2.imshow('fetch_window', fetch_frame)
        cv2.waitKey(5)

    def controller(self, command):
        match command:
            case "Open Hand":
                self.fetch.state_active = False
                self.spin.state_active = False
                self.sit.state_active = True
            case "Zero":
                self.sit.state_active = False
                self.fetch.state_active = False
                self.spin.state_active = True
            case "Peace Sign":
                self.sit.state_active = False
                self.spin.state_active = False
                self.fetch.state_active = True
            

 
 
def main(args=None):
    rclpy.init(args=args)
    node = GestureDetector("camera/image_raw")
    executor = MultiThreadedExecutor()
    executor.add_node(node)
    executor.add_node(node.fetch)
    executor.add_node(node.sit)
    executor.add_node(node.spin)
    try:
        executor.spin()
    finally:
        rclpy.shutdown()
    cv2.destroyAllWindows()
 
 
if __name__ == '__main__':
    main()
