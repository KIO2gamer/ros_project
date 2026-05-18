from typing import Dict

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from lab_assistant_robot.messages import from_msg, to_msg


class AuthNode(Node):
    def __init__(self) -> None:
        super().__init__('auth_node')
        self.declare_parameter('allowed_uids', ['A1B2C3D4'])
        self.declare_parameter('use_rc522', False)
        self.declare_parameter('rc522_poll_sec', 0.5)
        self.allowed_uids = set(self.get_parameter('allowed_uids').value)
        self.use_rc522 = bool(self.get_parameter('use_rc522').value)
        self.rc522_poll_sec = float(self.get_parameter('rc522_poll_sec').value)

        self.user_db: Dict[str, Dict[str, str]] = {
            'A1B2C3D4': {'name': 'Rana', 'role': 'student'},
            '11223344': {'name': 'Supervisor', 'role': 'admin'},
        }

        self.pub = self.create_publisher(String, '/auth/events', 10)
        self.ui_pub = self.create_publisher(String, '/ui/events', 10)
        self.create_subscription(String, '/auth/verify_cmd', self.on_verify, 10)

        self._reader = None
        self._last_uid = ''
        if self.use_rc522:
            self._init_rc522_reader()
            self.create_timer(self.rc522_poll_sec, self.poll_rc522)

    def on_verify(self, msg: String) -> None:
        payload = from_msg(msg)
        uid = payload.get('uid', '')
        if uid in self.allowed_uids:
            user = self.user_db.get(uid, {'name': 'Unknown', 'role': 'student'})
            self.pub.publish(to_msg({'event': 'authorized', 'uid': uid, **user}))
        else:
            self.pub.publish(to_msg({'event': 'denied', 'uid': uid}))

    def _init_rc522_reader(self) -> None:
        try:
            from mfrc522 import SimpleMFRC522  # type: ignore
            self._reader = SimpleMFRC522()
            self.get_logger().info('RC522 mode enabled.')
        except Exception as exc:
            self.use_rc522 = False
            self.get_logger().warn(f'RC522 unavailable, fallback to simulated input: {exc}')

    def poll_rc522(self) -> None:
        if not self.use_rc522 or self._reader is None:
            return
        try:
            uid, _ = self._reader.read_no_block()
            if not uid:
                return
            uid_text = str(uid)
            if uid_text == self._last_uid:
                return
            self._last_uid = uid_text
            self.ui_pub.publish(to_msg({'event': 'rfid_scan', 'uid': uid_text}))
            self.get_logger().info(f'RC522 detected UID: {uid_text}')
        except Exception as exc:
            self.get_logger().warn(f'RC522 read error: {exc}')


def main(args=None) -> None:
    rclpy.init(args=args)
    node = AuthNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
