#!/bin/bash

# See: https://vaneyckt.io/posts/safer_bash_scripts_with_set_euxo_pipefail/
set -Eeuo pipefail

readonly RED_BOLD='\033[1;31m'
readonly BLUE_BOLD='\033[1;34m'
readonly GREY_BOLD='\033[1;30m'
readonly YELLOW_BOLD='\033[1;33m'
readonly NC='\033[0m'

pushd deps

# PX4 Installation
echo -e "${YELLOW_BOLD}Installing PX4...${NC}"

bash ./PX4-Autopilot/Tools/setup/ubuntu.sh
pushd PX4-Autopilot
make px4_sitl

# uXRCE Installation
echo -e "${YELLOW_BOLD}uXRCE-Agent...${NC}"
popd
pushd Micro-XRCE-DDS-Agent

mkdir build
pushd build

cmake ..
make

sudo make install
sudo ldconfig /usr/local/lib

popd
popd




