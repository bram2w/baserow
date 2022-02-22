#!/usr/bin/env bash
set -Eeo pipefail

# A helper script which wraps another command, prepends each stdout/err line it prints
# with a specified PREFIX ($2), the current time and also colors the ousafe_tput ($1).

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

# shellcheck disable=SC2034
RED=$(safe_tput setaf 1)
# shellcheck disable=SC2034
GREEN=$(safe_tput setaf 2)
# shellcheck disable=SC2034
YELLOW=$(safe_tput setaf 3)
# shellcheck disable=SC2034
BLUE=$(safe_tput setaf 4)
# shellcheck disable=SC2034
PURPLE=$(safe_tput setaf 5)
# shellcheck disable=SC2034
CYAN=$(safe_tput setaf 6)
# shellcheck disable=SC2034
BOLD="$(safe_tput bold)"

NC=$(safe_tput sgr0) # No Color

COLOR=${!1}
shift

PREFIX=$1
shift

if [[ -n "${NO_COLOR:-}" ]]; then
  COLOR=
  NC=
fi

# We are going to replace this wrapper.sh process with the process defined by the
# args on the last line with the exec "$@". This is important as for signal handling
# to work properly supervisord needs to be the direct parent of the supervised process.
# However we also want any stdout/err from the new process to be run through the
# etc and sed commands to prepend a date time nicely colour them. What we do below is
# use exec first without a command which applies the redirections first to this shell.
# Then the final exec will inherit the redirection of stdout and err to ets/sed, whilst
# still becoming a direct child of supervisord.
exec > >(ets -f "[$PREFIX][%Y-%m-%d %H:%M:%S]" | sed -u $"s,.*,${COLOR}&${NC},")
exec 2> >(ets -f "[$PREFIX][%Y-%m-%d %H:%M:%S]" | sed -u $"s,.*,${COLOR}&${NC},")
exec "$@"
