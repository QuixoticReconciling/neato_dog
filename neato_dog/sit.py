import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
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
        '''
        Time-based loop for executing the sit sequence. Sequence is broken
        down into two steps: 0 (sit) and 1 (back up).
        '''
        
        # stop the loop if the state isn't active
        if not self.state_active:
            return

        # get current time and calculate elapsed time
        current_time = time.time()
        elapsed = current_time - self.start_time


        # break motion down into two steps
        # sit is step 0, back up is step 1
        if self.sit_step == 0:
            # stop for 0.5 seconds
            self.drive(linear=0.0, angular=0.0)
            if elapsed > 0.5:
                self.sit_step = 1 # switch to step 1
                self.start_time = time.time() # reset the time
                
        elif self.sit_step == 1:
            # drive backwards for 2 seconds
            self.drive(linear=-0.3, angular=0.0)
            if elapsed > 2:
                # stop 
                self.drive(linear=0.0, angular=0.0)
                self.get_logger().info("Sit sequence completed")
                self.state_active = False  # reset state to inactive
                self.sit_step = 0 # reset step to 0
                
        
    def drive(self, linear, angular):
        '''
        Creates and publishes a twist velocity message to the 'cmd_vel' topic.
        
        Args:
            linear (float): linear velocity(meters/second).
            angular (float): angular velocity (radians/second).
        '''
        
        vel = Twist()
        vel.linear.x = linear
        vel.angular.z = angular 
        self.publisher.publish(vel)
                 
def main(args=None):
    """Initialize our node, run it, cleanup on shut down"""
    rclpy.init(args=args)  # Initialize ROS2 network
    node = sitNode()  # Create our node
    rclpy.spin(node)  # Run our node
    rclpy.shutdown()  # If interrupted, gracefully shutdown the ROS2 network
    
if __name__ == '__main__':
    main()