import rclpy
from rclpy.node import Node
from time import sleep 
from geometry_msgs.msg import Twist 
import math 
from nav_msgs.msg import Odometry
from threading import Thread, Event
from tf_transformations import euler_from_quaternion 


# code format taken from robo-behaviors drive square 
class SpinNode(Node):
    
    def __init__(self):
        super().__init__("spin")
        # not sure why drive square1 works while drive square does not
        # prob bc smth with the cache

        self.state_active = False
        self.start_yaw = None

        self.publisher = self.create_publisher(Twist, 'cmd_vel', 10)
        self.odom_sub = self.create_subscription(Odometry, '/odom', self.odom_callback, 10)
        
        self.x = 0.0
        self.y = 0.0
        self.yaw = 0.0
        self.total_turned = 0.0
        self.odom_ready = False
        
        self.create_timer(0.1, self.run_loop)

    def odom_callback(self, msg):
        # receive messages from odom topic
        self.x = msg.pose.pose.position.x
        self.y = msg.pose.pose.position.y
        orientation_q = msg.pose.pose.orientation 
        # convert to rads
        orientation_list = [orientation_q.x, orientation_q.y, orientation_q.z, orientation_q.w]
        _, _, self.yaw = euler_from_quaternion(orientation_list)
        # give the ready signal
        self.odom_ready = True

    def run_loop(self):
        
        # used gemini to help combine functions
        if not self.state_active:
            return
            self.yaw = 0.0 #If it gets interrupted it gets set to 0
            self.total_turned

        if not self.odom_ready:
            self.get_logger().info("Waiting for odometry data...")
            return

        # Initialize start yaw on the first tick of the active state
        if self.start_yaw is None:
            self.get_logger().info('Starting 360 spin')
            self.start_yaw = self.yaw

        # Calculate angle turned non-blockingly
        self.total_turned += math.atan2(math.sin(self.yaw - self.start_yaw), math.cos(self.yaw - self.start_yaw))
        self.start_yaw = self.yaw
        
        if self.total_turned < 2 * math.pi:
            # Keep turning
            self.drive(linear=0.0, angular=0.7)
        else:
            # Stop and finish action
            self.drive(linear=0.0, angular=0.0)
            self.get_logger().info("360 spin completed")
            self.start_yaw = None
            self.total_turned = 0.0
            self.state_active = False

            
    def drive(self, linear, angular):
        vel = Twist()
        vel.linear.x = linear
        vel.angular.z = angular 
        self.publisher.publish(vel)

def main(args=None):
    """Initialize our node, run it, cleanup on shut down"""
    rclpy.init(args=args)  # Initialize ROS2 network
    node = SpinNode()  # Create our node
    rclpy.spin(node)  # Run our node
    rclpy.shutdown()  # If interrupted, gracefully shutdown the ROS2 network

if __name__ == '__main__':
    main()