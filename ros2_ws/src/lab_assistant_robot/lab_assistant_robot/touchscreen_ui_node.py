import tkinter as tk
from tkinter import ttk

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from lab_assistant_robot.messages import from_msg, to_msg


class TouchscreenUINode(Node):
    def __init__(self) -> None:
        super().__init__('touchscreen_ui_node')
        self.declare_parameter('enabled', True)
        self.enabled = bool(self.get_parameter('enabled').value)
        self.ui_pub = self.create_publisher(String, '/ui/events', 10)
        self.create_subscription(String, '/system/state', self.on_state, 10)

        self.stage = 'BOOT'
        self.user_name = '-'
        self.lab_mode = '-'

    def on_state(self, msg: String) -> None:
        payload = from_msg(msg)
        self.stage = payload.get('stage', 'UNKNOWN')
        user = payload.get('user', {})
        self.user_name = user.get('name', '-') if user else '-'
        self.lab_mode = payload.get('lab_mode', '-') or '-'

    def emit_rfid(self, uid: str) -> None:
        if not self.enabled:
            return
        self.ui_pub.publish(to_msg({'event': 'rfid_scan', 'uid': uid}))

    def emit_lab(self, lab: str) -> None:
        if not self.enabled:
            return
        self.ui_pub.publish(to_msg({'event': 'lab_selected', 'lab': lab}))

    def emit_request(self, item: str, qty: int) -> None:
        if not self.enabled:
            return
        self.ui_pub.publish(to_msg({'event': 'item_request', 'item': item, 'quantity': qty}))

    def emit_confirm(self) -> None:
        if not self.enabled:
            return
        self.ui_pub.publish(to_msg({'event': 'user_confirmed_dispense'}))


class TouchscreenApp:
    def __init__(self, node: TouchscreenUINode) -> None:
        self.node = node
        self.root = tk.Tk()
        self.root.title('Lab Assistant Touchscreen Test')
        self.root.geometry('900x540')

        self.stage_var = tk.StringVar(value='Stage: BOOT')
        self.user_var = tk.StringVar(value='User: -')
        self.lab_var = tk.StringVar(value='Lab: -')

        self.uid_var = tk.StringVar(value='A1B2C3D4')
        self.item_var = tk.StringVar(value='resistor_1k')
        self.qty_var = tk.IntVar(value=1)

        self.build_ui()
        self.root.after(60, self.tick)

    def build_ui(self) -> None:
        main = ttk.Frame(self.root, padding=16)
        main.pack(fill=tk.BOTH, expand=True)

        status = ttk.LabelFrame(main, text='System Status', padding=12)
        status.pack(fill=tk.X, pady=(0, 12))
        ttk.Label(status, textvariable=self.stage_var, font=('Segoe UI', 13, 'bold')).pack(anchor=tk.W)
        ttk.Label(status, textvariable=self.user_var).pack(anchor=tk.W)
        ttk.Label(status, textvariable=self.lab_var).pack(anchor=tk.W)

        auth = ttk.LabelFrame(main, text='Authentication', padding=12)
        auth.pack(fill=tk.X, pady=(0, 12))
        ttk.Label(auth, text='RFID UID').grid(row=0, column=0, padx=(0, 8), sticky='w')
        ttk.Entry(auth, textvariable=self.uid_var, width=20).grid(row=0, column=1, padx=(0, 8), sticky='w')
        ttk.Button(auth, text='Scan RFID', command=self.on_scan_rfid).grid(row=0, column=2, sticky='w')

        lab = ttk.LabelFrame(main, text='Lab Selection', padding=12)
        lab.pack(fill=tk.X, pady=(0, 12))
        ttk.Button(lab, text='Physics', command=lambda: self.node.emit_lab('physics')).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(lab, text='Chemistry', command=lambda: self.node.emit_lab('chemistry')).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(lab, text='Biology', command=lambda: self.node.emit_lab('biology')).pack(side=tk.LEFT)

        req = ttk.LabelFrame(main, text='Item Request', padding=12)
        req.pack(fill=tk.X, pady=(0, 12))
        ttk.Label(req, text='Item').grid(row=0, column=0, padx=(0, 8), sticky='w')
        ttk.Entry(req, textvariable=self.item_var, width=24).grid(row=0, column=1, padx=(0, 8), sticky='w')
        ttk.Label(req, text='Qty').grid(row=0, column=2, padx=(0, 8), sticky='w')
        ttk.Spinbox(req, from_=1, to=10, textvariable=self.qty_var, width=6).grid(row=0, column=3, padx=(0, 8), sticky='w')
        ttk.Button(req, text='Send Request', command=self.on_send_request).grid(row=0, column=4, sticky='w')

        dispense = ttk.LabelFrame(main, text='Dispense', padding=12)
        dispense.pack(fill=tk.X)
        ttk.Button(dispense, text='Confirm Dispense', command=self.node.emit_confirm).pack(side=tk.LEFT)

    def on_scan_rfid(self) -> None:
        self.node.emit_rfid(self.uid_var.get().strip())

    def on_send_request(self) -> None:
        self.node.emit_request(self.item_var.get().strip(), int(self.qty_var.get()))

    def tick(self) -> None:
        rclpy.spin_once(self.node, timeout_sec=0.0)
        self.stage_var.set(f'Stage: {self.node.stage}')
        self.user_var.set(f'User: {self.node.user_name}')
        self.lab_var.set(f'Lab: {self.node.lab_mode}')
        self.root.after(60, self.tick)

    def run(self) -> None:
        self.root.mainloop()


def main(args=None) -> None:
    rclpy.init(args=args)
    node = TouchscreenUINode()
    app = TouchscreenApp(node)
    try:
        app.run()
    finally:
        node.destroy_node()
        rclpy.shutdown()
