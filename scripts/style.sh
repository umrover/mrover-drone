#!/usr/bin/env bash

# See: https://vaneyckt.io/posts/safer_bash_scripts_with_set_euxo_pipefail/
set -Eeuo pipefail

shopt -s nullglob globstar
GLOBIGNORE="./deps/**:./build/**:./install/**:./venv/**"

readonly RED='\033[0;31m'
readonly NC='\033[0m'
readonly YELLOW_BOLD='\033[1;33m'

RUFF_EXCLUDES="deps,build,install,venv"
CLANG_FORMAT_ARGS=(
  "-style=file"
)

# Just do a dry run if the "fix" argument is not passed
FIX_MODE=false
if [ $# -gt 0 ] && [ "$1" == "--fix" ]; then
  FIX_MODE=true
  CLANG_FORMAT_ARGS+=("-i")
else
  CLANG_FORMAT_ARGS+=("--dry-run" "-Werror")
fi

function find_executable() {
  local -r executable="$1"
  local -r version="$2"
  local -r path=$(which "${executable}")
  if [ ! -x "${path}" ]; then
    echo -e "${RED}[Error] Could not find ${executable}${NC}" >&2
    exit 1
  fi
  if ! "${path}" --version | grep -q "${version}"; then
    echo -e "${RED}[Error] Wrong ${executable} version${NC}" >&2
    exit 1
  fi
  echo "${path}"
}

## Check that all tools are installed

CLANG_FORMAT_PATH=$(find_executable clang-format-18 18.1)
readonly CLANG_FORMAT_PATH
RUFF_PATH=$(find_executable ruff 0.17.4)

## Run checks

# Add new directories with C++ code here:
readonly CPP_FILES=(
  ./{drone_fc,drone_gs,drone_sim}/**/*.{cpp,hpp,h}
)

echo "Style checking C++ ..."
"${CLANG_FORMAT_PATH}" "${CLANG_FORMAT_ARGS[@]}" -i "${CPP_FILES[@]}"
echo "Done"

# Add new directories with Python code here:
readonly PYTHON_FILES=(
  ./{drone_fc,drone_gs,drone_sim,scripts}/**/*.py
  ./*.py
)

echo
if [ "$FIX_MODE" = true ]; then
  echo "Linting & Fixing python with ruff check ..."
  "${RUFF_PATH}" check --fix --line-length=120 --exclude="${RUFF_EXCLUDES}" .
  
  echo "Formatting Python with ruff format ..."
  "${RUFF_PATH}" format --line-length=120 --exclude="${RUFF_EXCLUDES}" .
else
  echo "Linting Python with ruff check (dry-run) ..."
  "${RUFF_PATH}" check --line-length=120 --exclude="${RUFF_EXCLUDES}" .

  echo "Formatting Python with ruff format ..."
  "${RUFF_PATH}" format --check --diff --line-length=120 --exclude="${RUFF_EXCLUDES}" .
fi
echo "Done"

if command -v shellcheck &> /dev/null; then
  echo
  echo "Linting bash scripts with shellcheck ..."
  readonly SHELL_FILES=(
    ./scripts/**/*.sh
    ./*.sh
  )
  # SC2155 is separate declaration and command.
  shellcheck --shell=bash --exclude=SC2155 "${SHELL_FILES[@]}"
  echo "Done"
fi

if [ "$FIX_MODE" = false ]; then
  echo
  echo -e "====================================================================="
  echo -e "${YELLOW_BOLD}Please run ./style.sh --fix if you want to actually update the files!${NC}"
  echo -e "====================================================================="
fi
