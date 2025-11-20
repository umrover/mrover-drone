#!/usr/bin/env python3
import os
from launch import LaunchDescription
from launch.actions import ExecuteProcess, SetEnvironmentVariable, DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration

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
        SetEnvironmentVariable("GZ_SIM_RESOURCE_PATH", resource_paths),
    ]

    # PX4 SITL process
    px4_process = ExecuteProcess(
        cmd=['./build/px4_sitl_default/bin/px4'],
        cwd=px4_dir,
        output="screen"
    )

    # Start ROS 2 <-> PX4 bridge (MicroRTPS Agent) 
    rtps_agent = ExecuteProcess(
        cmd=[
            'micrortps_agent', '-t', 'UDP',
            '-r', '14540',  # receive from PX4
            '-s', '14541'   # send to PX4
        ],
        output='screen'
    )

    # Optional QGroundControl
    qgc_path = find_qgc_appimage()
    qgc_process = None
    if qgc_path:
        qgc_process = ExecuteProcess(cmd=[qgc_path], output="screen")

    # Launch arguments
    actions = [
        DeclareLaunchArgument("sim_model", default_value="gz_x500"),
        DeclareLaunchArgument("world", default_value="default"),
    ]
    actions += env_actions
    actions.append(px4_process)
    if qgc_process:
        actions.append(qgc_process)

    return LaunchDescription(actions)
