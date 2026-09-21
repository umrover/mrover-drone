"""Launch the MAVROS offboard example node."""

from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    starter_project_mavros_node = Node(
        package="starter_project",
        executable="starter_project_mavros_node",
        name="starter_project_mavros_node",
        output="screen",
        parameters=[
            {
                "auto_offboard": False,
                "auto_arm": False,
                "mavros_prefix": "mavros/mavros",
                "mavros_plugin_prefix": "mavros/mavros",
            }
        ],
    )

    return LaunchDescription([
        starter_project_mavros_node,
    ])
