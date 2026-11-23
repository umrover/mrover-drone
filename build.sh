#!/usr/bin/env bash

set -euxo pipefail

build_profile=RelWithDebInfo

# choose build profile
if [[ "$#" -ne "0" ]]; then
    if [[ "$#" -eq "1" && ("$1" == "Release" || "$1" == "RelWithDebInfo" || "$1" == "Debug") ]]; then
        build_profile=$1
    else
        echo "Usage ./build.sh [Release|RelWithDebInfo|Debug]"
        exit 1
    fi
fi

echo "Using build profile: $build_profile"

# resolve repo path
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# inside ros2 workspace?
if [ "$(basename "$(dirname "${SCRIPT_DIR}")" = "src")" ]; then
    WS_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"
else
    # standalone clone - testing
    WS_DIR="${SCRIPT_DIR}"
fi

base_paths=()
for dir in "${SCRIPT_DIR}"/*; do
    [ -d "$dir" ] || continue
    case "$(basename "$dir")" in
        deps|build|install|log) continue ;;
    esac
    base_paths+=("$dir")
done
for dir in "${SCRIPT_DIR}"/deps/*; do
    [ -d "$dir" ] || continue
    # don't colcon build PX4
    [ "$(basename "$dir")" = "PX4-Autopilot" ] && continue
    base_paths+=("$dir")
done

# Build in the colcon workspace, not the package
pushd "${WS_DIR}"

cmake_args=(
    "-G" "Ninja"
    "-W" "no-dev"
    "-DCMAKE_BUILD_TYPE=${build_profile}"
    "-DCMAKE_EXPORT_COMPILE_COMMANDS=ON"
)

# automatically use ccache if installed
if command -v ccache &> /dev/null; then
    echo "ccache detected... Using compiler cache."
    cmake_args+=(
        "-DCMAKE_C_COMPILER_LAUNCHER=ccache"
        "-DCMAKE_CXX_COMPILER_LAUNCHER=ccache"
    )
fi

# invoke colcon
COLCON_EXTENSION_BLOCKLIST=colcon_core.event_handler.desktop_notification colcon build \
    --base-paths "${base_paths[@]}" \
    --cmake-args "${cmake_args[@]}" \
    --symlink-install \
    --event-handlers console_direct+ \
    --build-base "build/$build_profile" \
    --install-base "install/$build_profile" \

# symlink compile_commands.json into each package folder
for dir in "${SCRIPT_DIR}"/*/; do
    pkg=$(basename "$dir")
    if [ -f "build/${build_profile}/${pkg}/compile_commands.json" ]; then
        ln -sf "$(pwd)/build/${build_profile}/${pkg}/compile_commands.json" "${dir}compile_commands.json"
    fi
done

popd
echo "Drone workspace built successfully!"
