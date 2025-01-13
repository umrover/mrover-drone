#!/usr/bin/env bash

set -euxo pipefail

# navigate to workspace directory
pushd ../..

colcon build \
	--packages-select mrover_drone
	--symlink-install
