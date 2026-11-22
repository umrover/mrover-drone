#!/usr/bin/env bash

set -Eueo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

echo "=========================================="
echo "  MROVER Drone Setup"
echo "=========================================="

echo "[1/5] Updating Git submodules..."
git submodule update --init --recursive

base_paths=()
for dir in "${SCRIPT_DIR}"/*; do
    [ -d "$dir" ] || continue
    [ "$(basename "$dir")" = "deps" ] && continue
    base_paths+=("$dir")
done
for dir in "${SCRIPT_DIR}"/deps/*; do
    [ -d "$dir" ] || continue
    [ "$(basename "$dir")" = "PX4-Autopilot" ] && continue
    base_paths+=("$dir")
done

echo "[2/5] Installing system & ROS2 Jazzy dependecies..."
sudo apt-get update
sudo apt-get install -y \
    ninja-build \
    ccache \
    clang-format-18 \
    shellcheck \
    python3-rosdep \
    python3-pip \
    ros-jazzy-mavros \
    ros-jazzy-mavros-extras \
    ros-jazzy-mavros-msgs \
    ros-jazzy-rtcm-msgs

echo "Creating Python virtual env..."
if [ ! -d "${SCRIPT_DIR}/.venv" ]; then
    python3 -m venv --system-site-packages "${SCRIPT_DIR}/.venv"
fi
source "${SCRIPT_DIR}/.venv/bin/activate"

pip install --upgrade pip
pip install ruff==0.17.4 mypy==1.11.2

echo "[3/5] Installing MAVROS GeographicLib datasets..."
chmod +x ./scripts/install_geographiclib_datasets.sh
sudo ./scripts/install_geographiclib_datasets.sh

echo "[4/5] Installing rosdep..."
if [ ! -f "/etc/ros/rosdep/sources.list.d/20-default.list" ]; then
    sudo rosdep init
fi
rosdep update
# turn off u flag because setup.bash has some unset values
set +u
source /opt/ros/jazzy/setup.bash
set -u
rosdep install --from-paths "${base_paths[@]}" --ignore-src -r -y

echo "[5/5] Installing PX4 toolchain & building SITL..."
bash ./PX4-Autopilot/Tools/setup/ubuntu.sh
pushd ./deps/PX4-Autopilot
export CMAKE_POLICY_VERSION_MINIMUM=3.5
DONT_RUN=1 make px4_sitl gz_x500
popd

echo "=========================================="
echo "  Setup Complete! "
echo "=========================================="
