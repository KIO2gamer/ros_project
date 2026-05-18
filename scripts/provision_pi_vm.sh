#!/usr/bin/env bash
set -euo pipefail

MODE="${1:-test}"
RUN_MODE="${2:-run}"
ROS_DISTRO="${ROS_DISTRO:-humble}"
WORKSPACE="${WORKSPACE:-$HOME/physics_project/ros2_ws}"
PACKAGE_DIR="$WORKSPACE/src/lab_assistant_robot"
RUNTIME_PARAMS="$WORKSPACE/runtime_params.yaml"

if [[ "$MODE" != "test" && "$MODE" != "hardware" ]]; then
  echo "Usage: $0 [test|hardware] [run|no-run]"
  exit 1
fi

if [[ "$RUN_MODE" != "run" && "$RUN_MODE" != "no-run" ]]; then
  echo "Usage: $0 [test|hardware] [run|no-run]"
  exit 1
fi

if [[ ! -f "$PACKAGE_DIR/package.xml" ]]; then
  echo "Cannot find package at $PACKAGE_DIR"
  echo "Set WORKSPACE env var if needed."
  exit 1
fi

if [[ ! -f "/opt/ros/$ROS_DISTRO/setup.bash" ]]; then
  echo "ROS 2 $ROS_DISTRO not found at /opt/ros/$ROS_DISTRO/setup.bash"
  echo "Install ROS 2 first, then rerun this script."
  exit 1
fi

echo "Installing build and dependency tools..."
sudo apt update
sudo apt install -y python3-colcon-common-extensions python3-pip python3-rosdep

if [[ ! -f "/etc/ros/rosdep/sources.list.d/20-default.list" ]]; then
  sudo rosdep init || true
fi
rosdep update

source "/opt/ros/$ROS_DISTRO/setup.bash"
cd "$WORKSPACE"

echo "Installing package dependencies via rosdep..."
rosdep install --from-paths src --ignore-src -r -y

echo "Installing optional Python hardware libs..."
python3 -m pip install --user gpiozero mfrc522

echo "Building workspace..."
colcon build

USE_RC522="false"
USE_GPIO="false"
if [[ "$MODE" == "hardware" ]]; then
  USE_RC522="true"
  USE_GPIO="true"
fi

cat > "$RUNTIME_PARAMS" <<YAML
/**:
  ros__parameters:
    map_yaml: "maps/lab_map.yaml"

auth_node:
  ros__parameters:
    allowed_uids:
      - "A1B2C3D4"
      - "11223344"
    use_rc522: $USE_RC522
    rc522_poll_sec: 0.5

inventory_node:
  ros__parameters:
    max_quantity_default: 5

navigation_node:
  ros__parameters:
    obstacle_probability: 0.15

surveillance_node:
  ros__parameters:
    unsafe_mode: false

retrieval_node:
  ros__parameters:
    use_gpio: $USE_GPIO
    arm_pin: 18
    gripper_pin: 19
    action_time_sec: 0.8

dispense_node:
  ros__parameters:
    use_gpio: $USE_GPIO
    motor_pin: 23
    motor_time_sec: 0.7

battery_node:
  ros__parameters:
    low_threshold_percent: 20
    start_percent: 80

emergency_node:
  ros__parameters:
    simulate_after_sec: 0

mock_ui_node:
  ros__parameters:
    enabled: true

touchscreen_ui_node:
  ros__parameters:
    enabled: true
YAML

source "$WORKSPACE/install/setup.bash"

echo "Done."
echo "Runtime params file: $RUNTIME_PARAMS"
if [[ "$MODE" == "test" ]]; then
  LAUNCH_CMD="ros2 launch lab_assistant_robot vscode_touchscreen_test.launch.py params_file:=$RUNTIME_PARAMS"
else
  LAUNCH_CMD="ros2 launch lab_assistant_robot system_bringup.launch.py use_mock_ui:=false params_file:=$RUNTIME_PARAMS"
fi

echo "Launch command: $LAUNCH_CMD"

if [[ "$RUN_MODE" == "run" ]]; then
  echo "Starting ROS 2 launch now..."
  eval "$LAUNCH_CMD"
fi
