# Raspberry Pi 4 ROS 2 Lab Assistant (Flowchart Implementation)

This project implements your flowchart as a ROS 2 multi-node system with two run modes:

- simulation mode for quick development and debugging
- hardware mode for Raspberry Pi 4 integrations (RC522 and GPIO actuation)

## Package

- package: `lab_assistant_robot`
- orchestrator: `state_machine_node`
- core modules:
  - `auth_node` (RFID auth, simulation or RC522)
  - `inventory_node` (availability/permission/safety checks)
  - `navigation_node` (navigation simulation, obstacle event)
  - `surveillance_node` (safe/unsafe gate)
  - `retrieval_node` (simulation or GPIO arm+gripper)
  - `dispense_node` (simulation or GPIO motor)
  - `battery_node` (battery cycle and charge behavior)
  - `emergency_node` (interrupt path)
- UI options:
  - `mock_ui_node` (automatic test flow)
  - `touchscreen_ui_node` (interactive desktop touchscreen simulator)

## Launch Files

- `ros2_ws/src/lab_assistant_robot/launch/system_bringup.launch.py`
  - default full bringup with optional mock UI
- `ros2_ws/src/lab_assistant_robot/launch/vscode_touchscreen_test.launch.py`
  - full bringup plus clickable touchscreen test UI

## Build

```bash
cd ~/physics_project/ros2_ws
source /opt/ros/humble/setup.bash
colcon build
source install/setup.bash
```

## One-Command VM Provisioning

You can provision dependencies, build, generate runtime parameters, and launch in one step using:

bash scripts/provision_pi_vm.sh test

Hardware-mode provisioning and launch:

bash scripts/provision_pi_vm.sh hardware

If you only want setup and build without starting launch:

bash scripts/provision_pi_vm.sh test no-run

## Test In VS Code (Touchscreen UI)

Use this when you are coding and want to test interaction without physical touchscreen hardware.

```bash
cd ~/physics_project/ros2_ws
source /opt/ros/humble/setup.bash
source install/setup.bash
ros2 launch lab_assistant_robot vscode_touchscreen_test.launch.py
```

What you get:

- a desktop GUI window named `Lab Assistant Touchscreen Test`
- buttons for RFID scan, lab selection, item request, and dispense confirm
- live status labels showing stage, current user, and lab mode

To inspect state flow:

```bash
ros2 topic echo /system/state
```

## Raspberry Pi 4 Hardware Mode

Edit `ros2_ws/src/lab_assistant_robot/config/lab_rules.yaml` and switch these flags:

- `auth_node.use_rc522: true`
- `retrieval_node.use_gpio: true`
- `dispense_node.use_gpio: true`

Then run:

```bash
ros2 launch lab_assistant_robot system_bringup.launch.py use_mock_ui:=false
```

## Configuration

Tune runtime behavior in `ros2_ws/src/lab_assistant_robot/config/lab_rules.yaml`:

- auth: allowed UIDs, RC522 polling
- inventory: quantity limits
- navigation: obstacle probability
- retrieval: GPIO pins and movement timing
- dispense: GPIO pin and motor runtime
- battery: low threshold and start percent
- emergency: simulated trigger timing

## Notes

- RC522 and GPIO dependencies are optional; nodes fall back to simulation if imports fail.
- Emergency path is handled through `/emergency/events` and forces the state machine to emergency stop.
