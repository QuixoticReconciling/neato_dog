import rclpy
from rclpy.node import Node
from time import sleep 
from geometry_msgs.msg import Twist 
import math 
from std_msgs.msg import String
from nav_msgs.msg import Odometry
from neato2_interfaces.msg import Bump
from threading import Thread, Event
# code format taken from robo-behaviors drive square 
from neato_dog import gesture_node


class Idle(Node):
    
    def __init__(self):
        super().__init__("idle")
        # not sure why drive square1 works while drive square does not
        # prob bc smth with the cache

        self.state_active = True

        self.state_sub = self.create_subscription(String, 'state', self.process_state, 10)
        self.state_pub = self.create_publisher(String, 'state', 10)
        

        if self.state_active:
            self.create_timer(0.1, self.run_loop)


    def run_loop(self):
        if self.state_active:
            
            self.switch_state()
        else:
            print('inactive')
        

    def process_state(self, msg):
        if msg.data == 'IDLE':
            if not self.state_active:
                self.state_active = True
        else:
            self.state_active = False

    def switch_state(self, string):
        yum = String()
        yum.data = string
        self.state_pub.publish(yum)
        self.state_active = False
        print('state switched to idling')
            
def euler_from_quaternion(x, y, z, w):
    """
        Convert a quaternion into euler angles (roll, pitch, yaw)
        roll is rotation around x in radians (counterclockwise)
        pitch is rotation around y in radians (counterclockwise)
        yaw is rotation around z in radians (counterclockwise)
    """
    t0 = +2.0 * (w * x + y * z)
    t1 = +1.0 - 2.0 * (x * x + y * y)
    roll_x = math.atan2(t0, t1)

    t2 = +2.0 * (w * y - z * x)
    t2 = +1.0 if t2 > +1.0 else t2
    t2 = -1.0 if t2 < -1.0 else t2
    pitch_y = math.asin(t2)
     
    t3 = +2.0 * (w * z + x * y)
    t4 = +1.0 - 2.0 * (y * y + z * z)
    yaw_z = math.atan2(t3, t4)
     
    return roll_x, pitch_y, yaw_z # in radians
     
        
def main(args=None):
    """Initialize our node, run it, cleanup on shut down"""
    rclpy.init(args=args)  # Initialize ROS2 network
    node = DriveSquare1Node()  # Create our node
    rclpy.spin(node)  # Run our node
    rclpy.shutdown()  # If interrupted, gracefully shutdown the ROS2 network

if __name__ == '__main__':
    main()