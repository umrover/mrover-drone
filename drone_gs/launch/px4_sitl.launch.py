"""
Launch File for the uXRCE Agent
"""

from launch import LaunchDescription
from launch.actions import ExecuteProcess

def generate_launch_description() -> LaunchDescription:

    deps_directory = '/home/mrover-drone/ros2_ws/src/mrover_drone/deps/PX4-Autopilot'

    px4_sitl = ExecuteProcess(
        cmd=["make", "px4_sitl", "gz_x500"],
        shell=True,
        cwd=deps_directory
    )

    return LaunchDescription([
        px4_sitl
    ])