"""
Top Level Lauch File for SITL Simulation

Runs mavros, px4_sitl, uXRCE, and QGroundControl
"""

from launch_ros.substitutions import FindPackageShare

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import PathJoinSubstitution, TextSubstitution


def generate_launch_description() -> LaunchDescription:

    mavros = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([
                FindPackageShare('drone_gs'),
                'launch',
                'mavros.launch.py'
            ])
        ]),
        launch_arguments={
            "fcu_url": 'udp://:14445@'
        }.items()
    )

    px4_sitl = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([
                FindPackageShare('drone_gs'),
                'launch',
                'px4_sitl.launch.py'
            ])
        ])
    )

    qgc = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([
                FindPackageShare('drone_gs'),
                'launch',
                'qgc.launch.py'
            ])
        ])
    )

    uXRCE = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([
                FindPackageShare('drone_gs'),
                'launch',
                'uXRCE.launch.py'
            ])
        ])
    )

    return LaunchDescription([
        uXRCE,
        mavros,
        px4_sitl,
        qgc
    ])

