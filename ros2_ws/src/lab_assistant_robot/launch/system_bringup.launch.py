from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description() -> LaunchDescription:
    pkg_share = get_package_share_directory('lab_assistant_robot')
    default_params_file = os.path.join(pkg_share, 'config', 'lab_rules.yaml')
    params_file = LaunchConfiguration('params_file')
    use_mock_ui = LaunchConfiguration('use_mock_ui')

    return LaunchDescription([
        DeclareLaunchArgument('params_file', default_value=default_params_file),
        DeclareLaunchArgument('use_mock_ui', default_value='true'),
        Node(package='lab_assistant_robot', executable='state_machine_node', output='screen', parameters=[params_file]),
        Node(
            package='lab_assistant_robot',
            executable='mock_ui_node',
            output='screen',
            parameters=[params_file],
            condition=IfCondition(use_mock_ui),
        ),
        Node(package='lab_assistant_robot', executable='auth_node', output='screen', parameters=[params_file]),
        Node(package='lab_assistant_robot', executable='inventory_node', output='screen', parameters=[params_file]),
        Node(package='lab_assistant_robot', executable='navigation_node', output='screen', parameters=[params_file]),
        Node(package='lab_assistant_robot', executable='surveillance_node', output='screen', parameters=[params_file]),
        Node(package='lab_assistant_robot', executable='retrieval_node', output='screen', parameters=[params_file]),
        Node(package='lab_assistant_robot', executable='dispense_node', output='screen', parameters=[params_file]),
        Node(package='lab_assistant_robot', executable='battery_node', output='screen', parameters=[params_file]),
        Node(package='lab_assistant_robot', executable='emergency_node', output='screen', parameters=[params_file]),
    ])
