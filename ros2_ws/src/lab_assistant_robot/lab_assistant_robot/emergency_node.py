import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from lab_assistant_robot.messages import to_msg


class EmergencyNode(Node):
    def __init__(self) -> None:
        super().__init__('emergency_node')
        self.declare_parameter('simulate_after_sec', 0)
        self.simulate_after_sec = int(self.get_parameter('simulate_after_sec').value)
        self.triggered = False

        self.pub = self.create_publisher(String, '/emergency/events', 10)

        if self.simulate_after_sec > 0:
            self.create_timer(float(self.simulate_after_sec), self.trigger_once)

    def trigger_once(self) -> None:
        if self.triggered:
            return
        self.triggered = True
        self.pub.publish(to_msg({'detected': True, 'reason': 'Simulated emergency'}))


def main(args=None) -> None:
    rclpy.init(args=args)
    node = EmergencyNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
