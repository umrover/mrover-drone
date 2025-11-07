#!/usr/bin/env python3
import os
from launch import LaunchDescription
from launch.actions import ExecuteProcess, SetEnvironmentVariable, DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    # --- Configurable arguments ---
    sim_model = LaunchConfiguration('sim_model', default='x500')
    world = LaunchConfiguration('world', default='empty.sdf')

    # --- Paths ---
    px4_dir = os.getenv('PX4_HOME', os.path.expanduser('~/PX4-Autopilot'))
    build_dir = os.path.join(px4_dir, 'build', 'px4_sitl_default')
    px4_bin = os.path.join(build_dir, 'bin', 'px4')
    romfs = os.path.join(px4_dir, 'ROMFS/px4fmu_common')

    # --- Environment setup ---
    env_vars = {
        'PX4_SIM_MODEL': sim_model.perform(None),
        'PX4_GZ_MODEL': sim_model.perform(None),
        'PX4_GZ_WORLD': world.perform(None),
        'GZ_SIM_RESOURCE_PATH': os.path.join(px4_dir, 'Tools', 'gz', 'worlds'),
    }

    # --- Start Gazebo (Ignition / Gazebo 8.x) ---
    gz_sim = ExecuteProcess(
        cmd=['gz', 'sim', world],
        output='screen'
    )

    # --- Start PX4 SITL ---
    px4_process = ExecuteProcess(
        cmd=[px4_bin, romfs, '-s', 'etc/init.d-posix/rcS'],
        additional_env=env_vars,
        output='screen'
    )

    # --- Start ROS 2 <-> PX4 bridge (MicroRTPS Agent) ---
    rtps_agent = ExecuteProcess(
        cmd=[
            'micrortps_agent', '-t', 'UDP',
            '-r', '14540',  # receive from PX4
            '-s', '14541'   # send to PX4
        ],
        output='screen'
    )

    actions = [
        DeclareLaunchArgument('sim_model', default_value='x500', description='Vehicle model to simulate'),
        DeclareLaunchArgument('world', default_value='empty.sdf', description='Gazebo world file'),
    ]
    actions += [SetEnvironmentVariable(k, v) for k, v in env_vars.items()]
    actions += [gz_sim, px4_process, rtps_agent]

    return LaunchDescription(actions)
