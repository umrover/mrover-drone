"""
Launch file for the starter project node.
"""

from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import ExecuteProcess
from launch_ros.substitutions import FindPackagePrefix
from launch.substitutions import PathJoinSubstitution


def generate_launch_description() -> LaunchDescription:

    # Get the directory where PX4-Autopilot is located
    starter_project_pkg_dir = FindPackagePrefix("starter-project")

    deps_directory = PathJoinSubstitution(
        [starter_project_pkg_dir, '..', '..', 'deps', 'PX4-Autopilot']
    )

    px4_sitl = ExecuteProcess(
        cmd=["make", "px4_sitl", "gz_x500"],
        shell=True,
        cwd=deps_directory
    )

    uXRCE = ExecuteProcess(
        cmd=["MicroXRCEAgent", "udp4", "-p", "8888"],
        shell=True,
        cwd=deps_directory
    )

    starter_project_node = Node(
        package="starter-project",
        executable="starter_project_node",
        output="screen"
    )

    return LaunchDescription([
        px4_sitl,
        uXRCE,
        # starter_project_node
    ])