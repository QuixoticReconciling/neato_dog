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

        self.should_move = False  # whether the Neato should be moving

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
        cv2.namedWindow('image_info')
        # TODO: add trackbars to the binary_window GUI to set color filtering thresholds
        cv2.createTrackbar('red lower bound', 'binary_window', self.red_lower_bound, 255, self.set_red_lower_bound)
        cv2.createTrackbar('red upper bound', 'binary_window', self.red_upper_bound, 255, self.set_red_upper_bound)
        cv2.createTrackbar('green lower bound', 'binary_window', self.green_lower_bound, 255, self.set_green_lower_bound)
        cv2.createTrackbar('green upper bound', 'binary_window', self.green_upper_bound, 255, self.set_green_upper_bound)
        cv2.createTrackbar('blue lower bound', 'binary_window', self.blue_lower_bound, 255, self.set_blue_lower_bound)
        cv2.createTrackbar('blue upper bound', 'binary_window', self.blue_upper_bound, 255, self.set_blue_upper_bound)
        while True:
            self.run_loop()
            time.sleep(0.1)

    def set_red_lower_bound(self, val):
        """ A callback function to handle the OpenCV slider to select the red lower bound """
        self.red_lower_bound = val

    def set_red_upper_bound(self, val):
        """ A callback function to handle the OpenCV slider to select the red lower bound """
        self.red_upper_bound = val

    def set_green_lower_bound(self, val):
        """ A callback function to handle the OpenCV slider to select the red lower bound """
        self.green_lower_bound = val

    def set_green_upper_bound(self, val):
        """ A callback function to handle the OpenCV slider to select the red lower bound """
        self.green_upper_bound = val

    def set_blue_lower_bound(self, val):
        """ A callback function to handle the OpenCV slider to select the red lower bound """
        self.blue_lower_bound = val

    def set_blue_upper_bound(self, val):
        """ A callback function to handle the OpenCV slider to select the red lower bound """
        self.blue_upper_bound = val

    def process_mouse_event(self, event, x,y,flags,param):
        """ Process mouse events so that you can see the color values
            associated with a particular pixel in the camera images or 
            whether the Neato should move."""
        # scroll event for printing pixel data to the image info window
        img = 255*np.ones((500,500,3))
        self.image_info_window = img.astype('uint8')
        cv2.putText(self.image_info_window,
                    'Color (b=%d,g=%d,r=%d)' % (self.cv_image[y,x,0], self.cv_image[y,x,1], self.cv_image[y,x,2]),
                    (5,50),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0,0,0))

        # click event for controlling whether the Neato should move or not
        if event == cv2.EVENT_LBUTTONDOWN:
            self.should_move = not(self.should_move)

    def run_loop(self):
        """ Main loop for processing images and controlling the Neato through the CV interface."""
        # NOTE: only do cv2.imshow and cv2.waitKey in this function 
        if not self.cv_image is None:
            # TODO: modify this binary image filter line to take in user defined color filtering thresholds
            self.binary_image = cv2.inRange(self.cv_image, (self.blue_lower_bound,self.green_lower_bound,self.red_lower_bound), (self.blue_upper_bound,self.green_upper_bound,self.red_upper_bound))
            print(self.cv_image.shape)
            # TODO: compute the moments of the binary image and use them to find the center of the ball
            moments = cv2.moments(self.binary_image)
            if moments['m00'] != 0:
                self.center_x, self.center_y = moments['m10']/moments['m00'], moments['m01']/moments['m00']
                norm_x_pose = (self.center_x - self.cv_image.shape[1]/2) / self.cv_image.shape[1]
            # TODO: check whether or not the Neato should move and publish to cmd_vel accordingly
            msg_cmd = Twist()
            print(self.should_move)
            if self.should_move is True:
                msg_cmd.linear.x = 0.1
                msg_cmd.angular.z = -norm_x_pose
            self.pub.publish(msg_cmd)
            cv2.imshow('video_window', self.cv_image)
            cv2.imshow('binary_window', self.binary_image)
            if hasattr(self, 'image_info_window'):
                cv2.imshow('image_info', self.image_info_window)
            cv2.waitKey(5)

def main(args=None):
    rclpy.init()
    n = Fetch("camera/image") # Change depending on if your using gazebo or real neato
    rclpy.spin(n)
    rclpy.shutdown()


if __name__ == '__main__':
    main()