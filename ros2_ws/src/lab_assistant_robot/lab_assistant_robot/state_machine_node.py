from enum import Enum
from typing import Any, Dict

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from lab_assistant_robot.messages import from_msg, to_msg


class Stage(str, Enum):
    BOOT = "BOOT"
    STANDBY = "STANDBY"
    AUTH_IN_PROGRESS = "AUTH_IN_PROGRESS"
    WAITING_LAB_SELECTION = "WAITING_LAB_SELECTION"
    WAITING_ITEM_REQUEST = "WAITING_ITEM_REQUEST"
    INVENTORY_VALIDATION = "INVENTORY_VALIDATION"
    NAV_TO_SHELF = "NAV_TO_SHELF"
    SURVEILLANCE = "SURVEILLANCE"
    RETRIEVAL = "RETRIEVAL"
    RETURN_TO_USER = "RETURN_TO_USER"
    WAITING_CONFIRMATION = "WAITING_CONFIRMATION"
    DATABASE_UPDATE = "DATABASE_UPDATE"
    BATTERY_CHECK = "BATTERY_CHECK"
    CHARGING = "CHARGING"
    EMERGENCY_STOP = "EMERGENCY_STOP"


class LabSystemStateMachine(Node):
    def __init__(self) -> None:
        super().__init__('state_machine_node')

        self.stage = Stage.BOOT
        self.current_user: Dict[str, Any] = {}
        self.current_request: Dict[str, Any] = {}
        self.lab_mode = ''

        self.state_pub = self.create_publisher(String, '/system/state', 10)
        self.auth_cmd_pub = self.create_publisher(String, '/auth/verify_cmd', 10)
        self.inventory_cmd_pub = self.create_publisher(String, '/inventory/check_cmd', 10)
        self.nav_cmd_pub = self.create_publisher(String, '/nav/cmd', 10)
        self.surveillance_cmd_pub = self.create_publisher(String, '/surveillance/cmd', 10)
        self.retrieval_cmd_pub = self.create_publisher(String, '/retrieval/cmd', 10)
        self.dispense_cmd_pub = self.create_publisher(String, '/dispense/cmd', 10)
        self.database_cmd_pub = self.create_publisher(String, '/database/update_cmd', 10)
        self.alert_cmd_pub = self.create_publisher(String, '/alerts/cmd', 10)

        self.create_subscription(String, '/ui/events', self.on_ui_event, 10)
        self.create_subscription(String, '/auth/events', self.on_auth_event, 10)
        self.create_subscription(String, '/inventory/events', self.on_inventory_event, 10)
        self.create_subscription(String, '/nav/events', self.on_nav_event, 10)
        self.create_subscription(String, '/surveillance/events', self.on_surveillance_event, 10)
        self.create_subscription(String, '/retrieval/events', self.on_retrieval_event, 10)
        self.create_subscription(String, '/dispense/events', self.on_dispense_event, 10)
        self.create_subscription(String, '/battery/events', self.on_battery_event, 10)
        self.create_subscription(String, '/emergency/events', self.on_emergency_event, 10)

        self.create_timer(1.0, self.publish_state)
        self.create_timer(2.0, self.boot_sequence)
        self.boot_done = False

        self.get_logger().info('Flowchart state machine node started.')

    def set_stage(self, new_stage: Stage, reason: str) -> None:
        if self.stage == new_stage:
            return
        self.get_logger().info(f'{self.stage} -> {new_stage}: {reason}')
        self.stage = new_stage
        self.publish_state()

    def publish_state(self) -> None:
        self.state_pub.publish(to_msg({
            'stage': self.stage.value,
            'lab_mode': self.lab_mode,
            'user': self.current_user,
            'request': self.current_request,
        }))

    def boot_sequence(self) -> None:
        if self.boot_done:
            return
        self.boot_done = True
        self.get_logger().info('Power-on checks complete. Hardware initialized. Entering standby mode.')
        self.set_stage(Stage.STANDBY, 'System initialization completed')

    def on_ui_event(self, msg: String) -> None:
        payload = from_msg(msg)
        event = payload.get('event', '')

        if self.stage == Stage.EMERGENCY_STOP:
            return

        if event == 'rfid_scan' and self.stage == Stage.STANDBY:
            uid = payload.get('uid', '')
            self.set_stage(Stage.AUTH_IN_PROGRESS, 'RFID scanned')
            self.auth_cmd_pub.publish(to_msg({'command': 'verify_uid', 'uid': uid}))
            return

        if event == 'lab_selected' and self.stage == Stage.WAITING_LAB_SELECTION:
            self.lab_mode = payload.get('lab', '')
            self.set_stage(Stage.WAITING_ITEM_REQUEST, 'Lab configuration loaded')
            return

        if event == 'item_request' and self.stage == Stage.WAITING_ITEM_REQUEST:
            self.current_request = {
                'item': payload.get('item', ''),
                'quantity': int(payload.get('quantity', 1)),
                'lab_mode': self.lab_mode,
                'user_role': self.current_user.get('role', 'student'),
            }
            self.set_stage(Stage.INVENTORY_VALIDATION, 'Request sent to inventory management')
            self.inventory_cmd_pub.publish(to_msg({'command': 'validate_request', **self.current_request}))
            return

        if event == 'user_confirmed_dispense' and self.stage == Stage.WAITING_CONFIRMATION:
            self.dispense_cmd_pub.publish(to_msg({'command': 'dispense_item', **self.current_request}))
            return

    def on_auth_event(self, msg: String) -> None:
        payload = from_msg(msg)
        event = payload.get('event', '')

        if event == 'authorized' and self.stage == Stage.AUTH_IN_PROGRESS:
            self.current_user = {
                'uid': payload.get('uid', ''),
                'role': payload.get('role', 'student'),
                'name': payload.get('name', 'unknown'),
            }
            self.set_stage(Stage.WAITING_LAB_SELECTION, 'Access granted')
        elif event == 'denied':
            self.current_user = {}
            self.set_stage(Stage.STANDBY, 'Access denied')

    def on_inventory_event(self, msg: String) -> None:
        payload = from_msg(msg)
        event = payload.get('event', '')

        if event == 'request_invalid':
            self.set_stage(Stage.WAITING_LAB_SELECTION, 'Inventory/security restriction failed')
            return

        if event == 'request_valid' and self.stage == Stage.INVENTORY_VALIDATION:
            self.set_stage(Stage.NAV_TO_SHELF, 'Retrieval task generated')
            self.nav_cmd_pub.publish(to_msg({'command': 'go_to_shelf', **self.current_request}))

    def on_nav_event(self, msg: String) -> None:
        payload = from_msg(msg)
        event = payload.get('event', '')

        if event == 'obstacle_detected':
            self.get_logger().warn('Obstacle detected, path recalculation in progress.')
            return

        if event == 'reached_shelf' and self.stage == Stage.NAV_TO_SHELF:
            self.set_stage(Stage.SURVEILLANCE, 'Shelf reached')
            self.surveillance_cmd_pub.publish(to_msg({'command': 'start_monitoring'}))
            return

        if event == 'returned_to_user' and self.stage == Stage.RETURN_TO_USER:
            self.set_stage(Stage.WAITING_CONFIRMATION, 'Ready for user confirmation and dispense')
            return

        if event == 'reached_charger' and self.stage == Stage.CHARGING:
            self.get_logger().info('Robot docked at charging station.')

    def on_surveillance_event(self, msg: String) -> None:
        payload = from_msg(msg)
        event = payload.get('event', '')

        if event == 'unsafe_condition':
            self.enter_emergency_mode('Unsafe condition detected by surveillance')
            return

        if event == 'safe_to_retrieve' and self.stage == Stage.SURVEILLANCE:
            self.set_stage(Stage.RETRIEVAL, 'Area clear for item retrieval')
            self.retrieval_cmd_pub.publish(to_msg({'command': 'retrieve_item', **self.current_request}))

    def on_retrieval_event(self, msg: String) -> None:
        payload = from_msg(msg)
        event = payload.get('event', '')

        if event == 'retrieval_done' and self.stage == Stage.RETRIEVAL:
            self.set_stage(Stage.RETURN_TO_USER, 'Item in tray, returning to user')
            self.nav_cmd_pub.publish(to_msg({'command': 'return_to_user'}))
        elif event == 'retrieval_failed':
            self.set_stage(Stage.WAITING_ITEM_REQUEST, 'Retrieval failed, waiting for new request')

    def on_dispense_event(self, msg: String) -> None:
        payload = from_msg(msg)
        event = payload.get('event', '')

        if event == 'dispensed' and self.stage == Stage.WAITING_CONFIRMATION:
            self.set_stage(Stage.DATABASE_UPDATE, 'Item dispensed, updating records')
            self.database_cmd_pub.publish(to_msg({
                'command': 'write_transaction',
                'user': self.current_user,
                'request': self.current_request,
                'lab_mode': self.lab_mode,
            }))
            self.set_stage(Stage.BATTERY_CHECK, 'Checking battery status')

    def on_battery_event(self, msg: String) -> None:
        payload = from_msg(msg)
        low = bool(payload.get('low', False))
        charging_complete = bool(payload.get('charging_complete', False))

        if self.stage == Stage.BATTERY_CHECK:
            if low:
                self.set_stage(Stage.CHARGING, 'Battery low, navigating to charger')
                self.nav_cmd_pub.publish(to_msg({'command': 'go_charge'}))
            else:
                self.reset_to_standby('Battery healthy')
            return

        if self.stage == Stage.CHARGING and charging_complete:
            self.reset_to_standby('Charging completed')

    def on_emergency_event(self, msg: String) -> None:
        payload = from_msg(msg)
        if payload.get('detected', False):
            self.enter_emergency_mode(payload.get('reason', 'Emergency trigger'))
            return

        if payload.get('cleared', False) and self.stage == Stage.EMERGENCY_STOP:
            self.reset_to_standby('Emergency cleared')

    def enter_emergency_mode(self, reason: str) -> None:
        self.set_stage(Stage.EMERGENCY_STOP, reason)
        self.alert_cmd_pub.publish(to_msg({'command': 'alarm_on', 'reason': reason}))

    def reset_to_standby(self, reason: str) -> None:
        self.current_request = {}
        self.current_user = {}
        self.lab_mode = ''
        self.set_stage(Stage.STANDBY, reason)


def main(args=None) -> None:
    rclpy.init(args=args)
    node = LabSystemStateMachine()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
