#!/bin/bash
set -exo pipefail

# for colorful echos
RED="\e[1;31m"
GREEN="\e[1;32m"
BLUE="\e[1;34m"
NC="\e[0m"

echo -e "${BLUE}======= CONFIGURING DOCKER ENVIRONMENT =======${NC}"

echo -e "${GREEN}Setting up ROS2 workspace and building dependencies...${NC}"
cd /home/mrover/ros2_ws/

echo -e "${GREEN}Building PX4...${NC}"
PX4_DIR=/home/mrover/drone_deps/PX4-Autopilot
cd $PX4_DIR
make px4_sitl

## TODO: Add below to wiki section
# cd PX4-Autopilot
# git checkout v1.15.4
# cd ../px4_msgs
# git checkout release/1.15
# cd ../px4-ros2-interface-lib
# git checkout 1.4.0

# Check if the ROS_DISTRO is passed and use it
# to source the ROS environment
if [ -n "${ROS_DISTRO}" ]; then
	source "/opt/ros/$ROS_DISTRO/setup.bash"
fi
if [ ! -d "/etc/ros/rosdep/sources.list.d" ]; then
    rosdep init
fi
rosdep update

cd ~/ros2_ws
# Ensure the workspace directories exist
mkdir -p /home/mrover/ros2_ws/install
mkdir -p /home/mrover/ros2_ws/build
mkdir -p /home/mrover/ros2_ws/log

# Fix ownership of mounted volumes
sudo chown -R mrover:mrover /home/mrover/ros2_ws/install
sudo chown -R mrover:mrover /home/mrover/ros2_ws/build
sudo chown -R mrover:mrover /home/mrover/ros2_ws/log
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install --packages-select px4_msgs px4_ros2_cpp drone_sim
cd ~/ros2_ws/src/mrover_drone/deps/

## For Micro XRCE-DDS-Agent
sudo ldconfig /usr/local/lib

echo -e "${GREEN}Starting virtual X server...${NC}"
# Start virtual X server in the background
# - DISPLAY default is :99, set in dockerfile
# - Users can override with `-e DISPLAY=` in `docker run` command to avoid
#   running Xvfb and attach their screen
if [[ -x "$(command -v Xvfb)" && "$DISPLAY" == ":99" ]]; then
	echo "Starting Xvfb"
	Xvfb :99 -screen 0 1600x1200x24+32 &
fi


# Edit mavlink to set proper docker IP for mavlink
echo -e "${GREEN}Editing Mavlink config for container-QGC Connection...${NC}"
VM_HOST_IP=$(getent ahostsv4 host.docker.internal | head -1 |  awk '{ print $1 }')
QGC_PARAM="-t ${VM_HOST_IP}"
API_PARAM="-t ${VM_HOST_IP}"
CONFIG_FILE=${PX4_DIR}/build/px4_sitl_default/etc/init.d-posix/px4-rc.mavlink
sed -i "s/mavlink start \-x \-u \$udp_gcs_port_local -r 4000000/mavlink start -x -u \$udp_gcs_port_local -r 4000000 ${QGC_PARAM}/" ${CONFIG_FILE}
sed -i "s/mavlink start \-x \-u \$udp_offboard_port_local -r 4000000/mavlink start -x -u \$udp_offboard_port_local -r 4000000 ${API_PARAM}/" ${CONFIG_FILE}

export PATH=$PATH:/home/mrover/.local/bin
exec "$@"