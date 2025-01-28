"""
Launch File for the uXRCE Agent
"""

from launch import LaunchDescription
from launch.actions import ExecuteProcess

def generate_launch_description() -> LaunchDescription:
    uXRCE = ExecuteProcess(
        cmd=["MicroXRCEAgent", "udp4", "-p", "8888"],
        shell=True
    )

    return LaunchDescription([
        uXRCE
    ])