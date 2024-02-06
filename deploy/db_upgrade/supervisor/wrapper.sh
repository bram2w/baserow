#!/usr/bin/env bash
set -Eeo pipefail

# A helper script which wraps another command, prepends each stdout/err line it prints
# with a specified PREFIX ($2), the current time and also colors the output according
# to the first argument given to the script which should be one of the colours below.

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

if [[ -z "$BASEROW_RUN_MINIMAL" ]]; then
# Below is the magic that nicely formats the stdout and stderr of the command we will
# exec later.
#
# We are going to replace this wrapper.sh process with the process defined by the
# args on the last line with the exec "$@". This is important as for signal handling
# to work properly supervisord needs to be the direct parent of the supervised process.
#
# If we instead exec'd something like "$@ | awk ..." the process tree ends up looking
# like:
# supervisord -> bash $@ | awk -> $@.
# And so when supervisord tries to gracefully shut down its child it ends up sending
# signals to the dumb bash process which doesn't correctly pass them onto $@.
#
# To avoid this we can exec a process substitution to redirect this processes stderr
# and stdout into our nice wrapping command. Then when we exec the actual command which
# then inherits this processes file descriptors (redirections of stdout/err to awk).
# Importantly this way $@ is now the direct child process of supervisord and so will
# directly receive the correct shutdown signals. This means that postgres, redis, etc
# will all shutdown gracefully and correctly when supervisord tells them to do so, and
# we also get to nicely format their stdout and stderr!

# This awk works like so:
# 1. -vRS='[\r\n]' Sets AWK's record separator to split on newlines OR carriage returns,
#                  carriage returns are used to reset the current terminal line for
#                  progress bars. So to get awk properly flushing whenever one appears
#                  we need to separate using them also.
# 2. -vORS=''      Set the output record separator to empty as we are going to print it
#                  ourselves later.
# 3. { print       Start describing what awk should be printing per record
#     1.               Print the color code to color the output.
#     2.               Print the current time formatted.
#     3.               Print the actual log line from the wrapped command.
#     4.               Reset the color.
#     5.               Print the record separator for this record so either \r or \n
#                      depending on what $0 was separated by. By printing \r
#                      when the wrapped program generates one we ensure we get nice
#                      progress bar output.
# 4.               Finally force awk to flush its stdout and print so we don't get long
#                  pauses in log output due to buffering.
# 5. Redirect stderr to out so we format that nicely also. tqdm and gunicorn really
#    like logging to stderr (for diagnostic output like progress bars etc).
exec > >(gawk -vRS='[\r\n]' -vORS='' '{  print "'"${COLOR}"'",strftime("['"$PREFIX"'][%Y-%m-%d %H:%M:%S]"), $0, "'"${NC}"'" , RT; fflush(stdout)}') 2>&1
fi
exec "$@"
