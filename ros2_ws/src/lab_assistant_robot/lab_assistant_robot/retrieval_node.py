import time

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from lab_assistant_robot.messages import from_msg, to_msg


class RetrievalNode(Node):
    def __init__(self) -> None:
        super().__init__('retrieval_node')
        self.declare_parameter('use_gpio', False)
        self.declare_parameter('arm_pin', 18)
        self.declare_parameter('gripper_pin', 19)
        self.declare_parameter('action_time_sec', 0.8)

        self.use_gpio = bool(self.get_parameter('use_gpio').value)
        self.action_time_sec = float(self.get_parameter('action_time_sec').value)
        self.arm_pin = int(self.get_parameter('arm_pin').value)
        self.gripper_pin = int(self.get_parameter('gripper_pin').value)

        self.arm = None
        self.gripper = None
        if self.use_gpio:
            self._init_gpio()

        self.pub = self.create_publisher(String, '/retrieval/events', 10)
        self.create_subscription(String, '/retrieval/cmd', self.on_command, 10)

    def on_command(self, msg: String) -> None:
        payload = from_msg(msg)
        if payload.get('command') == 'retrieve_item':
            self.execute_retrieval()
            self.pub.publish(to_msg({'event': 'retrieval_done'}))

    def _init_gpio(self) -> None:
        try:
            from gpiozero import AngularServo, DigitalOutputDevice  # type: ignore
            self.arm = AngularServo(self.arm_pin, min_angle=0, max_angle=180)
            self.gripper = DigitalOutputDevice(self.gripper_pin)
            self.get_logger().info('Retrieval GPIO mode enabled.')
        except Exception as exc:
            self.use_gpio = False
            self.get_logger().warn(f'GPIO unavailable, retrieval simulation mode active: {exc}')

    def execute_retrieval(self) -> None:
        if not self.use_gpio or self.arm is None or self.gripper is None:
            return
        pause = max(0.05, self.action_time_sec / 2.0)
        self.arm.angle = 120
        time.sleep(pause)
        self.gripper.on()
        time.sleep(pause)
        self.arm.angle = 60
        time.sleep(pause)
        self.gripper.off()


def main(args=None) -> None:
    rclpy.init(args=args)
    node = RetrievalNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
