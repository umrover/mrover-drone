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
RUFF_ARGS=(
  "--line-length=120"
  "--exclude=deps,build,install,venv,.venv" 
)
if [ -f "${SCRIPT_DIR}/pyproject.toml" ]; then
  RUFF_ARGS+=("--config=${SCRIPT_DIR}/pyproject.toml")
else
  RUFF_ARGS+=("--isolated")
fi

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
  local -r path=$(command -v "${executable}" || true)
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
RUFF_PATH=$(find_executable ruff 0.17.5)
readonly RUFF_PATH

## Run checks

# Add new directories with C++ code here:
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
  "${RUFF_PATH}" check --fix "${RUFF_ARGS[@]}" .
  
  echo "Formatting Python with ruff format ..."
  "${RUFF_PATH}" format "${RUFF_ARGS[@]}" .
else
  echo "Linting Python with ruff check (dry-run) ..."
  "${RUFF_PATH}" check "${RUFF_ARGS[@]}" .

  echo "Formatting Python with ruff format ..."
  "${RUFF_PATH}" format --check --diff "${RUFF_ARGS[@]}" .
fi
echo "Done"

if command -v shellcheck &> /dev/null; then
  echo
  echo "Linting bash scripts with shellcheck ..."
  readonly SHELL_FILES=(
    ./**/*.sh
  )
  # SC2155 is separate declaration and command.
  if [ ${#SHELL_FILES[@]} -gt 0 ]; then
    shellcheck --shell=bash --exclude=SC2155 "${SHELL_FILES[@]}"
  fi
  echo "Done"
fi

if [ "$FIX_MODE" = false ]; then
  echo
  echo -e "====================================================================="
  echo -e "${YELLOW_BOLD}Please run ./style.sh --fix if you want to actually update the files!${NC}"
  echo -e "====================================================================="
fi
