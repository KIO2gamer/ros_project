import time

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from lab_assistant_robot.messages import from_msg, to_msg


class DispenseNode(Node):
    def __init__(self) -> None:
        super().__init__('dispense_node')
        self.declare_parameter('use_gpio', False)
        self.declare_parameter('motor_pin', 23)
        self.declare_parameter('motor_time_sec', 0.7)

        self.use_gpio = bool(self.get_parameter('use_gpio').value)
        self.motor_pin = int(self.get_parameter('motor_pin').value)
        self.motor_time_sec = float(self.get_parameter('motor_time_sec').value)
        self.motor = None
        if self.use_gpio:
            self._init_gpio()

        self.pub = self.create_publisher(String, '/dispense/events', 10)
        self.create_subscription(String, '/dispense/cmd', self.on_command, 10)

    def on_command(self, msg: String) -> None:
        payload = from_msg(msg)
        if payload.get('command') == 'dispense_item':
            self.run_dispense_motor()
            self.pub.publish(to_msg({'event': 'dispensed'}))

    def _init_gpio(self) -> None:
        try:
            from gpiozero import DigitalOutputDevice  # type: ignore
            self.motor = DigitalOutputDevice(self.motor_pin)
            self.get_logger().info('Dispense GPIO mode enabled.')
        except Exception as exc:
            self.use_gpio = False
            self.get_logger().warn(f'GPIO unavailable, dispense simulation mode active: {exc}')

    def run_dispense_motor(self) -> None:
        if not self.use_gpio or self.motor is None:
            return
        self.motor.on()
        time.sleep(max(0.05, self.motor_time_sec))
        self.motor.off()


def main(args=None) -> None:
    rclpy.init(args=args)
    node = DispenseNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
