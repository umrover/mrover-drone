"""
Launch File for the uXRCE Agent
"""

from launch import LaunchDescription
from launch.actions import ExecuteProcess
from launch.substitutions import LaunchConfiguration
from launch.actions import DeclareLaunchArgument

def generate_launch_description() -> LaunchDescription:

    xrce_port = LaunchConfiguration('xrce_port')

    xrce_port_arg = DeclareLaunchArgument(
        'xrce_port',
        default_value='8888',
        description="Port for the uXRCE agent to listen on (default 8888)"
    )

    uXRCE = ExecuteProcess(
        cmd=["MicroXRCEAgent", "udp4", "-p", "8888"],
        shell=True
    )

    return LaunchDescription([
        xrce_port_arg,
        uXRCE
    ])