from setuptools import find_packages, setup

package_name = 'lab_assistant_robot'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', ['launch/system_bringup.launch.py', 'launch/vscode_touchscreen_test.launch.py']),
        ('share/' + package_name + '/config', ['config/lab_rules.yaml']),
        ('share/' + package_name + '/maps', ['maps/lab_map.yaml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Your Name',
    maintainer_email='you@example.com',
    description='Flowchart-driven ROS 2 system for autonomous lab assistant robot.',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'state_machine_node = lab_assistant_robot.state_machine_node:main',
            'mock_ui_node = lab_assistant_robot.mock_ui_node:main',
            'auth_node = lab_assistant_robot.auth_node:main',
            'inventory_node = lab_assistant_robot.inventory_node:main',
            'navigation_node = lab_assistant_robot.navigation_node:main',
            'surveillance_node = lab_assistant_robot.surveillance_node:main',
            'retrieval_node = lab_assistant_robot.retrieval_node:main',
            'dispense_node = lab_assistant_robot.dispense_node:main',
            'battery_node = lab_assistant_robot.battery_node:main',
            'emergency_node = lab_assistant_robot.emergency_node:main',
            'touchscreen_ui_node = lab_assistant_robot.touchscreen_ui_node:main',
        ],
    },
)
