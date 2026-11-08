"""A script for driving a Neato towards an object of a particular color. 
Color is specified by a user setting color filtering thresholds."""
import os
import time
import numpy as np
import cv2
import rclpy

from threading import Thread, Event
from cv_bridge import CvBridge
from rclpy.node import Node
from sensor_msgs.msg import Image
from geometry_msgs.msg import Twist
from std_msgs.msg import Bool
from time import sleep

# Points the computer to local fonts for the QT GUI that OpenCV will produce.
os.environ['QT_QPA_FONTDIR'] = '/usr/share/fonts/truetype/dejavu'

class Fetch(Node):
    """ The BallTracker is a Python object that encompasses a ROS node 
        that can process images from the camera and search for a ball within.
        The node will issue motor commands to move forward while keeping
        the ball in the center of the camera's field of view. """

    def __init__(self, image_topic):
        """ Initialize the ball tracker """
        super().__init__('fetch')
        self.cv_image = None                        # the latest image from the camera
        self.bridge = CvBridge()                    # used to convert ROS messages to OpenCV

        self.create_subscription(Image, image_topic, self.process_image, 10)

        thread = Thread(target=self.loop_wrapper)
        thread.start()

        self.count = 0

    def process_image(self, msg):
        """ Process image messages from ROS and stash them in an attribute
            called cv_image for subsequent processing """
        self.cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")

    def loop_wrapper(self):
        """ This function takes care of calling the run_loop function repeatedly.
            We are using a separate thread to run the loop_wrapper to work around
            issues with single threaded executors in ROS2 """
        cv2.namedWindow('video_window')

        while True:
            self.run_loop()

            time.sleep(0.1)

    def run_loop(self):
        """ Main loop for processing images and controlling the Neato through the CV interface."""
        # NOTE: only do cv2.imshow and cv2.waitKey in this function 
        if self.cv_image is None:
            return

        frame = self.cv_image.copy()

        cv2.imshow('video_window', self.cv_image)

        if cv2.waitKey(5) & 0xFF == ord('s'):
            path = (f"/home/trevor/ros2_ws/src/neato_dog/neato_dog/calibration_photos/photo_{self.count}.jpg")
            cv2.imwrite(path, frame)
            if cv2.imwrite(path, frame):

                self.count+= 1
                print(f"Saved {path}")
            else:
                print("Didn't save properly")

        cv2.waitKey(5)

def main(args=None):
    rclpy.init()
    n = Fetch("camera/image_raw") # Change depending on if your using gazebo or real neato
    rclpy.spin(n)
    rclpy.shutdown()


if __name__ == '__main__':
    main()