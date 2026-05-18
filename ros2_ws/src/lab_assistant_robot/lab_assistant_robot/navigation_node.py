import random

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from lab_assistant_robot.messages import from_msg, to_msg


class NavigationNode(Node):
    def __init__(self) -> None:
        super().__init__('navigation_node')
        self.declare_parameter('obstacle_probability', 0.2)
        self.obstacle_probability = float(self.get_parameter('obstacle_probability').value)

        self.pub = self.create_publisher(String, '/nav/events', 10)
        self.create_subscription(String, '/nav/cmd', self.on_command, 10)

    def on_command(self, msg: String) -> None:
        payload = from_msg(msg)
        command = payload.get('command', '')

        if command == 'go_to_shelf':
            if random.random() < self.obstacle_probability:
                self.pub.publish(to_msg({'event': 'obstacle_detected'}))
            self.pub.publish(to_msg({'event': 'reached_shelf'}))

        elif command == 'return_to_user':
            self.pub.publish(to_msg({'event': 'returned_to_user'}))

        elif command == 'go_charge':
            self.pub.publish(to_msg({'event': 'reached_charger'}))


def main(args=None) -> None:
    rclpy.init(args=args)
    node = NavigationNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
