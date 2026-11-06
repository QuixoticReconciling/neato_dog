import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from geometry_msgs.msg import Twist
from sensor_msgs.msg import Image
import time
class sitNode(Node):
    '''
    Node class for handling the 'sit' state of the Neato dog.
    '''
    def __init__(self): 
        super().__init__('sitNode')
        
        self.state_active = False
        self.target_stop = 0.2
        self.target_slow = 0.4
        self.distance_to_obstacle = 0 
        
        self.vel = Twist()
        self.publisher = self.create_publisher(Twist, 'cmd_vel', 10)

        self.create_timer(0.1, self.run_loop)
        self.sit_step = 0
        self.start_time = 0.0
            
    def run_loop(self):
        
        if not self.state_active:
            return

        current_time = time.time()
        elapsed = current_time - self.start_time

        if self.sit_step == 0:
            # Step 0: Stop briefly before backing up
            self.drive(linear=0.0, angular=0.0)
            if elapsed > 0.5:
                self.sit_step = 1
                self.start_time = time.time()
                
        elif self.sit_step == 1:
            # Step 1: Drive backward for the calculated duration
            self.drive(linear=-0.3, angular=0.0)
            if elapsed > 2.67:
                # Maneuver completed: stop and reset state locally
                self.drive(linear=0.0, angular=0.0)
                self.get_logger().info("Sit sequence completed")
                self.state_active = False  # <--- Fixes the trapped state
                self.sit_step = 0
                
        
    def drive(self, linear, angular):
        vel = Twist()
        vel.linear.x = linear
        vel.angular.z = angular 
        self.publisher.publish(vel)
        
    def drive_forward(self, distance):
        forward_vel = -0.3
        self.drive(linear = forward_vel, angular = 0.0)
        
        duration = distance / forward_vel
        
        self.drive(linear = 0.0, angular = 0.0)
       
            
def main(args=None):
    """Initialize our node, run it, cleanup on shut down"""
    rclpy.init(args=args)  # Initialize ROS2 network
    node = sitNode()  # Create our node
    rclpy.spin(node)  # Run our node
    rclpy.shutdown()  # If interrupted, gracefully shutdown the ROS2 network
    
if __name__ == '__main__':
    main()