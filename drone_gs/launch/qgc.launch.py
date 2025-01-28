"""
Launch File for QGroundControl
"""

from launch import LaunchDescription
from launch.actions import ExecuteProcess

def generate_launch_description() -> LaunchDescription:
    qgroundcontrol = ExecuteProcess(
        cmd=['/home/mrover-drone/Desktop/QGroundControl.AppImage'], # path to QGroundControll AppImage
        shell=True
    )

    return LaunchDescription([
        qgroundcontrol
    ])