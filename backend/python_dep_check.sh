#!/bin/bash
# Bash strict mode: http://redsymbol.net/articles/unofficial-bash-strict-mode/
set -euo pipefail

# Currently we only define our direct dependencies in requirements/base.txt and
# requirements/dev.txt. This means that pip figures out and resolves the versions of
# dependant libraries for us based on the constraints of our direct dependencies.
# This means a seemingly simple change to base.txt or dev.txt can result in important
# dependencies having their versions change under the hood with us being non the wiser.
#
# This file is a temporary solution and is used by our `make lint` command and a new
# file requirements/dev_frozen.txt to clearly show and enforce what exactly all of our
# python dependencies, direct and indirect are. Really we should switch away from just
# using pip to something like Poetry which has a lock file built in.

FROZEN_DEP_FILE="requirements/dev_frozen.txt"

if [ -t 0 ]; then
  TPUTTERM=()
else
  # if we are in a non-interactive environment set a default -T for tput so it doesn't
  # crash
  TPUTTERM=(-T xterm-256color)
fi

safe_tput(){
  tput "${TPUTTERM[@]}" "$@"
}

RED=$(safe_tput setaf 1)
GREEN=$(safe_tput setaf 2)
YELLOW=$(safe_tput setaf 3)
NC=$(safe_tput sgr0) # No Color

if [[ "${1:-}" == "check" ]]; then
  FROZEN_DEPS=$(< "$FROZEN_DEP_FILE")
  NEW_DEPS=$(pip freeze)
  if [[ "$FROZEN_DEPS" != "$NEW_DEPS" ]]; then
      echo "$RED Python dependencies have changed but $FROZEN_DEP_FILE " \
           "has not been updated, please run$NC$GREEN make pip-clean-reinstall-and-freeze and commit " \
           "$NC$RED so we can clearly see any changed python dependencies. See below " \
           "for diff:${NC}"
      diff  <(echo "$FROZEN_DEPS" ) <(echo "$NEW_DEPS")
      exit 1
  else
    echo "$GREEN No python dep changes detected $NC"
  fi
elif [[ "${1:-}" == "freeze" ]]; then
  if [ ! -d /baserow/venv ]; then
    echo "Please run inside the backend docker container, couldn't find the venv."
    exit 1
  fi
  rm -rf /baserow/venv
  python3 -m virtualenv /baserow/venv
  . /baserow/venv/bin/activate
  pip install -r requirements/base.txt
  pip install -r requirements/dev.txt
  pip freeze > "$FROZEN_DEP_FILE"
  echo "$GREEN Successfully froze current python deps to $FROZEN_DEP_FILE $NC"
  exit 0
else
  echo "$YELLOW Supported arguments are check or freeze, unknown args provided. $NC"
  exit 1
fi

