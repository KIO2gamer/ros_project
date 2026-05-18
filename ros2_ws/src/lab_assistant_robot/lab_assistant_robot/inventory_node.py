from typing import Dict

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from lab_assistant_robot.messages import from_msg, to_msg


class InventoryNode(Node):
    def __init__(self) -> None:
        super().__init__('inventory_node')
        self.declare_parameter('max_quantity_default', 5)
        self.max_quantity_default = int(self.get_parameter('max_quantity_default').value)

        self.stock: Dict[str, int] = {
            'resistor_1k': 100,
            'oscilloscope_probe': 6,
            'beaker_100ml': 20,
            'high_voltage_supply': 1,
            'laser_source': 2,
        }

        self.student_restricted = {'high_voltage_supply'}
        self.lab_restricted = {'physics': {'laser_source'}}

        self.pub = self.create_publisher(String, '/inventory/events', 10)
        self.create_subscription(String, '/inventory/check_cmd', self.on_check, 10)

    def on_check(self, msg: String) -> None:
        payload = from_msg(msg)
        item = payload.get('item', '')
        qty = int(payload.get('quantity', 1))
        role = payload.get('user_role', 'student')
        lab_mode = payload.get('lab_mode', 'physics')

        if qty <= 0 or qty > self.max_quantity_default:
            self.pub.publish(to_msg({'event': 'request_invalid', 'reason': 'Quantity out of range'}))
            return

        available = self.stock.get(item, 0)
        if available < qty:
            self.pub.publish(to_msg({'event': 'request_invalid', 'reason': 'Insufficient stock'}))
            return

        if role == 'student' and item in self.student_restricted:
            self.pub.publish(to_msg({'event': 'request_invalid', 'reason': 'Permission denied'}))
            return

        if item in self.lab_restricted.get(lab_mode, set()):
            self.pub.publish(to_msg({'event': 'request_invalid', 'reason': 'Lab safety restriction'}))
            return

        self.stock[item] = available - qty
        self.pub.publish(to_msg({'event': 'request_valid', 'task': {'item': item, 'quantity': qty}}))


def main(args=None) -> None:
    rclpy.init(args=args)
    node = InventoryNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
