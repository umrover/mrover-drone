#!/usr/bin/env python3
import os
from launch import LaunchDescription
from launch.actions import ExecuteProcess, SetEnvironmentVariable, DeclareLaunchArgument, TimerAction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def find_qgc_appimage():
    search_paths = [
        os.path.expanduser("~/ros2_ws/src/"),
        os.path.expanduser("~/Downloads")
    ]
    for root in search_paths:
        for dirpath, _, filenames in os.walk(root):
            for f in filenames:
                if "QGroundControl" in f and f.endswith(".AppImage"):
                    return os.path.join(dirpath, f)
    return None

def generate_launch_description():
    # Launch configurations
    sim_model = LaunchConfiguration('sim_model')
    world     = LaunchConfiguration('world')
    verbose_sim = LaunchConfiguration('verbose')

    px4_dir = os.getenv(
        "PX4_HOME",
        os.path.expanduser("~/ros2_ws/src/mrover_drone/deps/PX4-Autopilot")
    )

    ws_root = os.path.expanduser("~/ros2_ws")

    resource_paths = os.pathsep.join([
        os.path.join(px4_dir, "Tools/simulation/gz/models"),
        os.path.join(px4_dir, "Tools/simulation/gz/worlds"),
        os.path.join(ws_root, "src/mrover_drone/drone_sim/worlds"),
        os.path.join(ws_root, "src/mrover_drone/drone_sim/models"),
    ])

    # Environment variables
    env_actions = [
        SetEnvironmentVariable("PX4_SYS_AUTOSTART", "4001"),
        SetEnvironmentVariable("PX4_SIM_MODEL", sim_model),
        SetEnvironmentVariable("PX4_GZ_MODEL", sim_model),
        SetEnvironmentVariable("PX4_GZ_WORLD", world),
        SetEnvironmentVariable("PX4_SITL_WORLD", world),
        SetEnvironmentVariable("PX4_HOME", px4_dir),
        SetEnvironmentVariable("VERBOSE_SIM", verbose_sim),
        SetEnvironmentVariable("GZ_SIM_RESOURCE_PATH", resource_paths),
    ]

    # PX4 SITL process
    px4_process = ExecuteProcess(
        cmd=['./build/px4_sitl_default/bin/px4'],
        cwd=px4_dir,
        output="screen"
    )

    # Start ROS 2 <-> PX4 bridge (MicroXRCE Agent) 
    rtps_agent = TimerAction(
        period=5.0,
        actions=[
            ExecuteProcess(
                cmd=['MicroXRCEAgent', 'udp4', '-p', '8888'],
                cwd=px4_dir,
                output='screen'
            )
        ]
    )

    # TODO: Add event handler to run this before px4.
    move_world_to_px4_dir = Node(
        package='drone_sim',
        executable='symlink_world.sh',
        namespace='symlink_world',
        arguments=[world],
        output='screen',
        cwd=os.path.expanduser("~/ros2_ws/src/mrover_drone/drone_sim")
    )

    # Optional QGroundControl
    qgc_path = find_qgc_appimage()
    print(qgc_path)
    qgc_process = None
    if qgc_path:
        qgc_process = ExecuteProcess(cmd=[qgc_path], output="screen")

    # Launch arguments
    actions = [
        DeclareLaunchArgument("sim_model", default_value="gz_x500"),
        DeclareLaunchArgument("world", default_value="default"),
        DeclareLaunchArgument("verbose", default_value="1"),
    ]
    actions += env_actions
    actions.append(move_world_to_px4_dir)
    actions.append(px4_process)
    actions.append(rtps_agent)
    if qgc_process:
        actions.append(qgc_process)

    return LaunchDescription(actions)
