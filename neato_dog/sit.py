""""
Sit
--------

"""

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from sensor_msgs.msg import LaserScan
import math
from std_msgs.msg import String
from time import sleep

class Sit(Node):
    """
    A node used to determine whether an object the neato bumped into is a wall or not
    """
    def __init__(self):
        super().__init__('detect_wall_node')
        self.create_timer(0.1, self.run_loop)
        self.sub = self.create_subscription(LaserScan, 'scan', self.process_scan, 10)
        self.pub = self.create_publisher(Twist, 'cmd_vel', 10)

        self.behavior_pub = self.create_publisher(String, 'behavior', 10)
        self.create_subscription(String, 'behavior', self.process_behavior, 10)
        self.state = 'detecting'
        self.is_wall = False
        self.active = False
        self.first_adjust = True
        self.ticks = 0
        self.is_adjusted = False


        self.get_logger().info("I'm initializing")

    def process_behavior(self, msg):
            """
            takes input from the behavior topic and adjusts output of node as needed
            """
            if msg.data == 'DETECT_WALL':
                if not self.active:
                    self.state = 'detecting'
                    self.is_wall = False
                    self.first_adjust = True
                    self.ticks = 0
                    self.is_adjusted = False
                self.active = True
            else: 
                self.active = False

    def hand_off(self, next_name):
        """
        Transfers functionality to the next node
        """
        self.pub.publish(Twist())
        self.active = False
        state_msg = String()
        state_msg.data = next_name
        self.behavior_pub.publish(state_msg)
        self.get_logger().info(f"handing off to {next_name}")


    def run_loop(self):
        """
        adjusts the neato to the correct orientation after a bump as occured
        """
        if self.active == False:
            return
        msg = Twist()
        if self.state == 'detecting':
            pass
        elif self.state == 'adjust':
            self.get_logger().info("Now adjusting")
            if self.first_adjust == True:
                msg.linear.x = -0.1
                sleep(2)
                self.first_adjust = False
            msg.angular.z = 30 * math.pi /180
            if self.is_adjusted:
                self.hand_off('WALL_FOLLOW')
                self.first_adjust = True
                return
        elif self.state == 'backup':
            msg.linear.x = -0.1
            self.ticks = self.ticks + 1
            if self.ticks >= 15:
                self.ticks = 0
                self.state = 'turn_around'
        elif self.state == 'turn_around':
            msg.angular.z = 30 * math.pi /180
            self.ticks = self.ticks + 1
            if self.ticks >= 60:
                self.hand_off('DRAW_SHAPE')
                self.first_adjust = True
                return
        self.pub.publish(msg)
        
    def process_scan(self, msg):
        """
        tracks the current state of the robot
        """
        self.get_logger().info("We are scanning")
        if self.active == False:
            return
        if self.state == 'detecting':
            self.detect_the_wall(msg)
            if self.is_wall:
                self.state = 'adjust'
                self.get_logger().info("We got a wall")
            else:
                self.state = 'backup'
        elif self.state == 'adjust':
            self.adjust_neato(msg)


    def detect_the_wall(self, msg):
        """
        Does the math calculations (with an error) to determine if the bumped into 
        object is a wall. Projects a 30 degree cone from the smallest distance from the neato
        """
        if self.active == False:
            return
        error = .2
        min_dist = 100 # avoid inf
        min_dist_idx = 0
        self.get_logger().info(f"active: {str(self.active)}")
        for idx, distance in enumerate(msg.ranges):
            if 0 < distance < min_dist:
                min_dist = distance
                min_dist_idx = idx

        plus45 = min_dist_idx + 30
        if plus45 >= 360:
            plus45 = plus45 - 360

        minus45 = min_dist_idx - 30

        if minus45 < 0:
            minus45 = minus45 + 360

        self.get_logger().info(f"side 1 bearing: {minus45}. side 1 distance: {msg.ranges[minus45]}")
        self.get_logger().info(f"side 2 bearing: {plus45}. side 2 distance: {msg.ranges[plus45]}")
            
        if math.fabs(msg.ranges[minus45] - msg.ranges[plus45]) < error:
            self.get_logger().info("WALL YEYAY")
            self.is_wall = True
        else:
            self.get_logger().info("NO WALL SAD")
            self.is_wall = False

    def adjust_neato(self, msg):
        """
        Adjusts the neato in segments until it is parallel with the wall
        """
        min_dist = 100
        min_dist_idx = 0
        for idx, distance in enumerate(msg.ranges):
            if distance < min_dist:
                min_dist = distance
                min_dist_idx = idx

        if math.fabs(min_dist_idx - 90) < 15:
            self.is_adjusted = True 
              
        self.get_logger().info(f"min distance: {min_dist}")        

def main(args=None):
    rclpy.init(args=args)
    node = Sit()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == '__main__':
    main()
