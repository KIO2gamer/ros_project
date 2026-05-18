import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from lab_assistant_robot.messages import from_msg, to_msg


class SurveillanceNode(Node):
    def __init__(self) -> None:
        super().__init__('surveillance_node')
        self.declare_parameter('unsafe_mode', False)
        self.unsafe_mode = bool(self.get_parameter('unsafe_mode').value)

        self.pub = self.create_publisher(String, '/surveillance/events', 10)
        self.create_subscription(String, '/surveillance/cmd', self.on_command, 10)

    def on_command(self, msg: String) -> None:
        payload = from_msg(msg)
        if payload.get('command') != 'start_monitoring':
            return

        if self.unsafe_mode:
            self.pub.publish(to_msg({'event': 'unsafe_condition'}))
        else:
            self.pub.publish(to_msg({'event': 'safe_to_retrieve'}))


def main(args=None) -> None:
    rclpy.init(args=args)
    node = SurveillanceNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
