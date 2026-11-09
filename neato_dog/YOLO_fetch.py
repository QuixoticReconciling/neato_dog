"""A script for driving a Neato towards an object of a particular color. 
Color is specified by a user setting color filtering thresholds."""
import os
import numpy as np
import cv2
import rclpy

from ultralytics import YOLO
from cv_bridge import CvBridge
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from sensor_msgs.msg import Image
from geometry_msgs.msg import Twist

# Points the computer to local fonts for the QT GUI that OpenCV will produce.
os.environ['QT_QPA_FONTDIR'] = '/usr/share/fonts/truetype/dejavu'

class Fetch(Node):

    def __init__(self, image=None):
        """ Initialize the node """
        super().__init__('fetch')


        self.cv_image = None        # the latest image from the camera
        self.bridge = CvBridge()    # used to convert ROS messages to OpenCV
        self.final = None

        """You'll notice that this path is different than the one used in the test script
        marker_detection.py. This is because when running the program, it was using up too
        much processing power and we had to shrink the image size from 640 to 320. We did
        this by running the following commands in terminal:
        """
        self.model = YOLO(os.path.expanduser(
    "~/ros2_ws/src/neato_dog/neato_dog/YOLO_model/best_openvino_model/"))
        self.model(np.zeros((320, 320, 3), dtype=np.uint8), imgsz=320, verbose=False) #call to warmup YOLO

        self.state_active = False

        #This if block is straight from Claude in an attempt to increase framerate. This only keeps the newest frame.
        if image is not None:
            qos = QoSProfile(depth=1, reliability=ReliabilityPolicy.BEST_EFFORT,
                            history=HistoryPolicy.KEEP_LAST)
            self.create_subscription(Image, image, self.callback, qos)


        # Publishing to the velocity of the robot and a separate image that allows us to see what YOLO sees.
        self.vel_pub = self.create_publisher(Twist, 'cmd_vel', 10)
        self.img_pub = self.create_publisher(Image, "ultralytics/detection/image", 5)

        # Initialize attributes for the center of the ball
        self.center_x = 0.
        self.center_y = 0.

        self.norm_x_pose = 0.0

        self.create_timer(0.05, self.loop_wrapper)

    def callback(self, message):
        """The callback function takes the output from ROS and turns it into an
        OpenCV image that YOLO can do its object detection on."""

        self.cv_image = self.bridge.imgmsg_to_cv2(message, desired_encoding="bgr8")

    def loop_wrapper(self):
        """Since running the model requires a lot of computing power this loop wrapper
        ensures that it only runs when the state is active."""
        if self.state_active and self.cv_image is not None:
            self.run_loop()
        elif self.state_active:
            print("fetch node active but no image yet")

    def drive(self, linear, angular):
        """This function publishes to '/cmd_vel' and lets the robot drive 
        at any linear or angular speed."""

        msg = Twist()
        msg.linear.x = linear
        msg.angular.z = angular
        self.vel_pub.publish(msg)

    def run_loop(self):
        """ This main loop takes the OpenCV/Numpy array that has already been converted in callback
        and then runs our custom YOLO model on it. If the model recognizes ano boject, it will steer 
        in the direction of that object. If there is no bounding box, it will spin and search until
        it finds something."""
        frame = self.cv_image
        result = self.model(frame, imgsz=320, verbose=False)[0]

        if len(result.boxes) == 0: #YOLO finds nothing in frame
            self.final = frame
            self.drive(linear = 0.0, angular = 0.3)
        else:                       # YOLO finds a red expo marker in frame
            x_center = float(result.boxes.xywh[0][0]) #boxes gives a tensor. Must convert to python number
            self.norm_x_pose = (x_center - self.cv_image.shape[1]/2) / self.cv_image.shape[1] # Normalizes the center in relation to the image
            self.final = result.plot()              # Draw the bounding box around the object
            self.drive(linear = 0.1, angular = -self.norm_x_pose)   #Steer the robot in the direction of the bounding box    

        # This is here so we can actually see what YOLO is seeing
        self.img_pub.publish(self.bridge.cv2_to_imgmsg(self.final, encoding="bgr8"))

def main(args=None):
    rclpy.init()
    n = Fetch("camera/image_raw") # Change depending on if your using gazebo or real neato
    rclpy.spin(n)
    rclpy.shutdown()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    main()