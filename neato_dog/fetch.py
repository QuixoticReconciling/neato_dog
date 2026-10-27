"""A script for driving a Neato towards an object of a particular color. 
Color is specified by a user setting color filtering thresholds."""
import os
import time
import numpy as np
import cv2
import rclpy

from threading import Thread
from cv_bridge import CvBridge
from rclpy.node import Node
from sensor_msgs.msg import Image
from geometry_msgs.msg import Twist

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
        self.pub = self.create_publisher(Twist, 'cmd_vel', 10)

        self.obj_detected = True  # whether the Neato should be moving

        # TODO: initialize attributes for the center of the ball
        self.center_x = 0.
        self.center_y = 0.
        # TODO: initialize attributes for the color filtering thresholds
        self.red_lower_bound = 45
        self.red_upper_bound = 60
        self.blue_lower_bound = 80
        self.blue_upper_bound = 100
        self.green_lower_bound = 50
        self.green_upper_bound = 75

        thread = Thread(target=self.loop_wrapper)
        thread.start()

    def process_image(self, msg):
        """ Process image messages from ROS and stash them in an attribute
            called cv_image for subsequent processing """
        self.cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")

    def loop_wrapper(self):
        """ This function takes care of calling the run_loop function repeatedly.
            We are using a separate thread to run the loop_wrapper to work around
            issues with single threaded executors in ROS2 """
        cv2.namedWindow('video_window')
        cv2.namedWindow('binary_window')

        while True:
            self.run_loop()
            time.sleep(0.1)

    def process_mouse_event(self, event, x,y,flags,param):
        """ Process mouse events to control when the Neato should move."""

        # click event for controlling whether the Neato should move or not
        # if event == cv2.EVENT_LBUTTONDOWN:
        #     self.should_move = not(self.should_move)

    def search(self):
        msg = Twist()
        msg.angular.z = 0.1
        self.pub.publish(msg)

    def shape_found(self, binary_image):
        # if binary_image contains white
        #     self.should_move is True

        pass

    def run_loop(self):
        """ Main loop for processing images and controlling the Neato through the CV interface."""
        # NOTE: only do cv2.imshow and cv2.waitKey in this function 
        if not self.cv_image is None:
            self.binary_image = cv2.inRange(
                self.cv_image, 
                (self.blue_lower_bound, self.green_lower_bound, self.red_lower_bound), 
                (self.blue_upper_bound, self.green_upper_bound, self.red_upper_bound)
                )
            # computes the moments of the binary image and use them to find the center of the ball
            moments = cv2.moments(self.binary_image)
            if moments['m00'] != 0:
                self.center_x, self.center_y = moments['m10']/moments['m00'], moments['m01']/moments['m00']
                norm_x_pose = (self.center_x - self.cv_image.shape[1]/2) / self.cv_image.shape[1]
            # Spin the neato
            #self.search()
            msg_cmd = Twist()
            print(self.obj_detected)
            if self.obj_detected is True:
                msg_cmd.linear.x = 0.1
                msg_cmd.angular.z = -norm_x_pose
            self.pub.publish(msg_cmd)
            cv2.imshow('video_window', self.cv_image)
            cv2.imshow('binary_window', self.binary_image)
            cv2.waitKey(5)

def main(args=None):
    rclpy.init()
    n = Fetch("camera/image") # Change depending on if your using gazebo or real neato
    rclpy.spin(n)
    rclpy.shutdown()


if __name__ == '__main__':
    main()