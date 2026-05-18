from typing import Optional

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from lab_assistant_robot.messages import from_msg, to_msg


class MockUINode(Node):
    def __init__(self) -> None:
        super().__init__('mock_ui_node')
        self.declare_parameter('enabled', True)
        self.enabled = bool(self.get_parameter('enabled').value)

        self.ui_pub = self.create_publisher(String, '/ui/events', 10)
        self.create_subscription(String, '/system/state', self.on_state, 10)

        self.last_stage: Optional[str] = None
        self.last_action_time = self.get_clock().now()

        self.get_logger().info('Mock UI node started.')

    def on_state(self, msg: String) -> None:
        if not self.enabled:
            return

        payload = from_msg(msg)
        stage = payload.get('stage', '')
        if stage == self.last_stage:
            return

        self.last_stage = stage
        if stage == 'STANDBY':
            self.ui_pub.publish(to_msg({'event': 'rfid_scan', 'uid': 'A1B2C3D4'}))
        elif stage == 'WAITING_LAB_SELECTION':
            self.ui_pub.publish(to_msg({'event': 'lab_selected', 'lab': 'physics'}))
        elif stage == 'WAITING_ITEM_REQUEST':
            self.ui_pub.publish(to_msg({'event': 'item_request', 'item': 'resistor_1k', 'quantity': 1}))
        elif stage == 'WAITING_CONFIRMATION':
            self.ui_pub.publish(to_msg({'event': 'user_confirmed_dispense'}))


def main(args=None) -> None:
    rclpy.init(args=args)
    node = MockUINode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
