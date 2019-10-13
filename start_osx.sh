#!/bin/bash

tabname() {
  printf "\e]1;$1\a"
}

new_tab() {
  TAB_NAME=$1
  COMMAND=$2
  CONTAINER_COMMAND=$3

  osascript \
      -e "tell application \"Terminal\"" \
      -e "tell application \"System Events\" to keystroke \"t\" using {command down}" \
      -e "do script \"printf '\\\e]1;$TAB_NAME\\\a'; $COMMAND\" in front window" \
      -e "do script \"$CONTAINER_COMMAND\" in front window" \
      -e "end tell" > /dev/null
}

docker-compose up -d

new_tab "Backend" \
        "docker exec -it backend bash" \
        "python src/baserow/manage.py runserver 0.0.0.0:8000"

new_tab "Web frontend" \
        "docker exec -it web-frontend bash" \
        "yarn run dev"

new_tab "Web frontend eslint" \
        "docker exec -it web-frontend bash" \
        "yarn run eslint --fix"

new_tab "Old web frontend" \
        "docker exec -it old-web-frontend bash" \
        "yarn run dev"
