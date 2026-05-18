import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from lab_assistant_robot.messages import from_msg, to_msg


class BatteryNode(Node):
    def __init__(self) -> None:
        super().__init__('battery_node')
        self.declare_parameter('low_threshold_percent', 20)
        self.declare_parameter('start_percent', 80)

        self.low_threshold = int(self.get_parameter('low_threshold_percent').value)
        self.level = int(self.get_parameter('start_percent').value)
        self.charging = False

        self.pub = self.create_publisher(String, '/battery/events', 10)
        self.create_subscription(String, '/nav/events', self.on_nav_event, 10)
        self.create_timer(5.0, self.on_tick)

    def on_nav_event(self, msg: String) -> None:
        payload = from_msg(msg)
        if payload.get('event') == 'reached_charger':
            self.charging = True

    def on_tick(self) -> None:
        if self.charging:
            self.level = min(100, self.level + 15)
        else:
            self.level = max(0, self.level - 2)

        low = self.level <= self.low_threshold
        charging_complete = self.charging and self.level >= 95
        if charging_complete:
            self.charging = False

        self.pub.publish(to_msg({
            'level': self.level,
            'low': low,
            'charging_complete': charging_complete,
        }))


def main(args=None) -> None:
    rclpy.init(args=args)
    node = BatteryNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
