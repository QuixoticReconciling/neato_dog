"""A script where the neato takes pictures."""
import os
import cv2
import rclpy

from cv_bridge import CvBridge
from rclpy.node import Node
from sensor_msgs.msg import Image

# Points the computer to local fonts for the QT GUI that OpenCV will produce.
os.environ['QT_QPA_FONTDIR'] = '/usr/share/fonts/truetype/dejavu'

class Snap(Node):
    """ The BallTracker is a Python object that encompasses a ROS node 
        that can process images from the camera and search for a ball within.
        The node will issue motor commands to move forward while keeping
        the ball in the center of the camera's field of view. """

    def __init__(self, image_topic):
        """ Initialize the node """
        super().__init__('snap')
        self.cv_image = None                        # the latest image from the camera
        self.bridge = CvBridge()                    # used to convert ROS messages to OpenCV

        self.create_subscription(Image, image_topic, self.process_image, 10)    # Subscribe to the image
        self.create_timer(0.05, self.run_loop)

        self.count = 0

    def process_image(self, msg):
        """ Process image messages from ROS and stash them in an attribute
            called cv_image for subsequent processing """
        self.cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")

    def run_loop(self):
        """ Main loop for taking pictures and saving them in the calibration photos folder."""
        if self.cv_image is None:
            return

        # Create a copy of the frame to write with
        frame = self.cv_image.copy()

        cv2.imshow('video_window', self.cv_image)

        # The key to take a snapshot is 's'
        if cv2.waitKey(5) & 0xFF == ord('s'):
            # A path to write to
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
    n = Snap("camera/image_raw")
    rclpy.spin(n)
    rclpy.shutdown()


if __name__ == '__main__':
    main()