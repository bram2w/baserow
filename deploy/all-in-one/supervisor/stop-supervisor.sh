#!/usr/bin/env bash
set -Eeo pipefail

# This file implements and follows supervisord's eventlistener protocol which has
# specific requirements for what is written to STDOUT. Please ensure all stdout follows
# the protocol as defined in http://supervisord.org/events.html#event-listeners-and-event-notifications
printf "READY\n";

while read -r; do
  echo -e "\e[31mBaserow was stopped or one of it's services crashed, see the logs above for more details. \e[0m" >&2
  kill -SIGTERM "$(cat supervisord.pid)"
done < /dev/stdin
