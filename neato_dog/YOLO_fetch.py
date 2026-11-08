"""A script for driving a Neato towards an object of a particular color. 
Color is specified by a user setting color filtering thresholds."""
import os
import time
import numpy as np
import cv2
import rclpy
import cv_bridge

from ultralytics import YOLO
from threading import Thread, Event
from cv_bridge import CvBridge
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
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

    def __init__(self, image):
        """ Initialize the ball tracker """
        super().__init__('fetch')
        self.cv_image = None                        # the latest image from the camera
        self.bridge = CvBridge()                    # used to convert ROS messages to OpenCV
        self.final = None
        self.model = YOLO(os.path.expanduser("~/ros2_ws/src/neato_dog/neato_dog/YOLO_model/best.pt"))

        self.state_active = False

        
        self.shape_found = Event()

        self.create_subscription(Image, image, self.callback, qos_profile_sensor_data)
        self.vel_pub = self.create_publisher(Twist, 'cmd_vel', 10)
        self.img_pub = self.create_publisher(Image, "ultralytics/detection/image", 5)

        # Initialize attributes for the center of the ball
        self.center_x = 0.
        self.center_y = 0.

        self.norm_x_pose = 0.0

        thread = Thread(target=self.loop_wrapper, daemon=True)
        thread.start()

    def callback(self, message):
        """Publish the annotated camera frame. From Ulytralytics ROS 
        quickstart guide: https://docs.ultralytics.com/guides/ros-quickstart"""

        self.cv_image = self.bridge.imgmsg_to_cv2(message, desired_encoding="bgr8")
        print(f"image: {message.width}x{message.height}, shape={self.cv_image.shape}")
        result = self.model(self.cv_image)[0]

        if not result:
            print("No bounding box")
            self.shape_found.clear()
            self.final = self.cv_image
        else:
            x_center = float(result.boxes.xywh[0][0]) #boxes gives a tensor. Must convert to python number
            self.norm_x_pose = (x_center - self.cv_image.shape[1]/2) / self.cv_image.shape[1]
            self.final = result.plot()
            self.shape_found.set()

        self.img_pub.publish(self.bridge.cv2_to_imgmsg(self.final, encoding="bgr8"))

    def loop_wrapper(self):
        """ This function takes care of calling the run_loop function repeatedly.
            We are using a separate thread to run the loop_wrapper to work around
            issues with single threaded executors in ROS2 """
        # print("loop wrapper started")


        while True:
            if self.state_active:
                self.run_loop()

            time.sleep(0.1)

    def drive(self, linear, angular):
        msg = Twist()
        msg.linear.x = linear
        msg.angular.z = angular
        self.vel_pub.publish(msg)

    def run_loop(self):
        """ Main loop for processing images and controlling the Neato through the CV interface."""
        if not self.state_active:
            return
        
        #print(f"run_loop: cv_image None? {self.cv_image is None}, final None? {self.final is None}")
        # NOTE: only do cv2.imshow and cv2.waitKey in this function 
            # computes the moments of the binary image and use them to find the center of the ball
        if  self.shape_found.is_set():
            self.drive(linear=0.1, angular = -self.norm_x_pose)

        else:
            self.drive(linear= 0.0, angular = 0.1)

        #print(f"final: type={type(self.final)}, shape={getattr(self.final, 'shape', None)}, dtype={getattr(self.final, 'dtype', None)}")

def main(args=None):
    rclpy.init()
    n = Fetch("camera/image_raw") # Change depending on if your using gazebo or real neato
    rclpy.spin(n)
    rclpy.shutdown()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    main()