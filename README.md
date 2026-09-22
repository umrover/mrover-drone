# MRover Drone

This is the main repo for the MRover Drone subteam's source code. Check out the wiki for setup and deployment.

## Starter Project

After completing the ROS 2 tutorials, use the `starter-project` package to learn how a ROS 2 node can control PX4 through MAVROS.

The package contains:

- `starter-project/src/starter_project_mavros_node.cpp`: the MAVROS offboard controller
- `starter-project/launch/starter_project.launch.py`: launches the controller node
- `drone_gs/launch/mavros.launch.py`: launches MAVROS and connects it to PX4

The ROS package name is `starter_project`, even though its source directory is named `starter-project`.

The data flow is:

```text
PX4 <-> MAVLink <-> MAVROS <-> ROS 2 starter_project_mavros_node
```

The node receives the vehicle state and local pose from MAVROS, publishes local position setpoints, and advances through a list of XYZ waypoints. The default points form a 2 m square relative to the starting position. PX4 remains responsible for stabilizing the vehicle and producing motor commands.

### Build

```zsh
cd ~/ros2_ws
unset AMENT_CURRENT_PREFIX AMENT_PREFIX_PATH COLCON_PREFIX_PATH
source /opt/ros/jazzy/setup.zsh
colcon build --symlink-install --packages-select starter_project drone_gs
source ~/ros2_ws/install/setup.zsh
```

### Run

Start PX4 SITL first. In a separate terminal, start MAVROS using the MAVLink endpoint exposed by PX4:

```zsh
cd ~/ros2_ws
unset AMENT_CURRENT_PREFIX AMENT_PREFIX_PATH COLCON_PREFIX_PATH
source /opt/ros/jazzy/setup.zsh
source ~/ros2_ws/install/setup.zsh
ros2 launch drone_gs mavros.launch.py \
	fcu_url:='udp://:14540@127.0.0.1:14580'
```

Then start the controller in another terminal:

```zsh
cd ~/ros2_ws
source /opt/ros/jazzy/setup.zsh
source ~/ros2_ws/install/setup.zsh
ros2 launch starter_project starter_project.launch.py
```

The launch file publishes setpoints but leaves automatic OFFBOARD mode changes and arming disabled. Test in SITL first and confirm the vehicle state in QGroundControl before enabling autonomous control.

To enable the node's OFFBOARD and arming requests explicitly:

```zsh
ros2 run starter_project starter_project_mavros_node \
	--ros-args -p auto_offboard:=true -p auto_arm:=true
```

Keep an RC override and PX4 failsafe configured whenever testing on hardware.
