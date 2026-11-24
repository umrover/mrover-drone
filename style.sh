#!/usr/bin/env bash

# See: https://vaneyckt.io/posts/safer_bash_scripts_with_set_euxo_pipefail/
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

shopt -s nullglob globstar
GLOBIGNORE="./deps/**:./build/**:./install/**:./venv/**:./.venv/**:./.git/**"

readonly RED='\033[0;31m'
readonly NC='\033[0m'
readonly YELLOW_BOLD='\033[1;33m'

CLANG_FORMAT_ARGS=(
  "-style=file:${SCRIPT_DIR}/.clang-format"
)

# Just do a dry run if the "fix" argument is not passed
FIX_MODE=false
if [ $# -gt 0 ] && [ "$1" == "--fix" ]; then
  FIX_MODE=true
  CLANG_FORMAT_ARGS+=("-i")
else
  CLANG_FORMAT_ARGS+=("--dry-run" "--Werror")
fi

function find_executable() {
  local -r executable="$1"
  local -r version="$2"
  local -r install_hint="$3"
  local -r path=$(command -v "${executable}" || true)
  if [ ! -x "${path}" ]; then
    echo -e "${RED}[Error] Could not find ${executable}. Install with: ${install_hint}${NC}" >&2
    exit 1
  fi
  if ! "${path}" --version | grep -qwF "${version}"; then
    echo -e "${RED}[Error] Wrong ${executable} version (expected ${version}). Install with: ${install_hint}${NC}" >&2
    exit 1
  fi
  echo "${path}"
}

## Check that all tools are installed
CLANG_FORMAT_PATH=$(find_executable clang-format-18 "18.1" "sudo apt install clang-format-18")
readonly CLANG_FORMAT_PATH
RUFF_PATH=$(find_executable ruff "0.17.5" "pip install ruff==0.17.5")
readonly RUFF_PATH

## Run checks

readonly CPP_FILES=(
  ./**/*.{cpp,hpp,h}
)

echo "Style checking C++ ..."
if [ ${#CPP_FILES[@]} -gt 0 ]; then
  "${CLANG_FORMAT_PATH}" "${CLANG_FORMAT_ARGS[@]}" -i "${CPP_FILES[@]}"
fi
echo "Done"

echo
if [ "$FIX_MODE" = true ]; then
  echo "Linting & Fixing python with ruff check ..."
  "${RUFF_PATH}" check --fix .
  
  echo "Formatting Python with ruff format ..."
  "${RUFF_PATH}" format .
else
  echo "Linting Python with ruff check (dry-run) ..."
  "${RUFF_PATH}" check .

  echo "Formatting Python with ruff format ..."
  "${RUFF_PATH}" format --check --diff .
fi
echo "Done"

if command -v shellcheck &> /dev/null; then
  echo
  echo "Linting bash scripts with shellcheck ..."
  # SC2155 is separate declaration and command.
  # only checking style.sh; there are errors in some old sh files
  shellcheck --shell=bash --exclude=SC2155 ./style.sh
  echo "Done"
fi

if [ "$FIX_MODE" = false ]; then
  echo
  echo -e "====================================================================="
  echo -e "${YELLOW_BOLD}Please run ./style.sh --fix if you want to actually update the files!${NC}"
  echo -e "====================================================================="
fi
