"""A script for driving a Neato towards an object of a particular color. 
Color is specified by a user setting color filtering thresholds."""
import os
import time
import numpy as np
import cv2
import rclpy
import cv_bridge
import traceback

from ultralytics import YOLO
from threading import Thread, Event
from cv_bridge import CvBridge
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
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

    def __init__(self, image=None):
        """ Initialize the ball tracker """
        super().__init__('fetch')


        self.cv_image = None                        # the latest image from the camera
        self.bridge = CvBridge()                    # used to convert ROS messages to OpenCV
        self.final = None
        self.model = YOLO(os.path.expanduser(
    "~/ros2_ws/src/neato_dog/neato_dog/YOLO_model/best_openvino_model/"))
        self.model(np.zeros((320, 320, 3), dtype=np.uint8), imgsz=320, verbose=False) #call to warmup YOLO

        self.state_active = False

        
        self.shape_found = Event()

        #qos is straight from claude trying to increase framerate. This only keeps the newest frame.
        
        if image is not None:
            qos = QoSProfile(depth=1, reliability=ReliabilityPolicy.BEST_EFFORT,
                            history=HistoryPolicy.KEEP_LAST)
            self.create_subscription(Image, image, self.callback, qos)
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

    def loop_wrapper(self):
        while True:
            if self.state_active and self.cv_image is not None:
                try:
                    self.run_loop()
                except Exception:
                    self.get_logger().error(traceback.format_exc())
                time.sleep(0.01)
            else:
                if self.state_active:
                    self.get_logger().warn("fetch active but no image yet",
                                        throttle_duration_sec=2.0)
                time.sleep(0.1)

    def drive(self, linear, angular):
        msg = Twist()
        msg.linear.x = linear
        msg.angular.z = angular
        self.vel_pub.publish(msg)

    def run_loop(self):
        """ Main loop for processing images and controlling the Neato through the CV interface."""
        frame = self.cv_image
        result = self.model(frame, imgsz=320, verbose=False)[0]

        if len(result.boxes) == 0: #YOLO finds nothing in frame
            self.final = frame
            self.drive(linear = 0.0, angular = 0.3)
        else:
            x_center = float(result.boxes.xywh[0][0]) #boxes gives a tensor. Must convert to python number
            self.norm_x_pose = (x_center - self.cv_image.shape[1]/2) / self.cv_image.shape[1]
            self.final = result.plot()
            self.drive(linear = 0.1, angular = -self.norm_x_pose)

        self.img_pub.publish(self.bridge.cv2_to_imgmsg(self.final, encoding="bgr8"))

def main(args=None):
    rclpy.init()
    n = Fetch("camera/image_raw") # Change depending on if your using gazebo or real neato
    rclpy.spin(n)
    rclpy.shutdown()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    main()