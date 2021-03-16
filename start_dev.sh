#!/bin/bash

tabname() {
  printf "\e]1;$1\a"
}

print_manual_instructions(){
  COMMAND=$1
  CONTAINER_COMMAND=$2
  echo -e "\nOpen a new tab/terminal and run:"
  echo "    $COMMAND"
  echo "Then inside the container run:"
  echo "    $CONTAINER_COMMAND"
}

PRINT_WARNING=true
new_tab() {
  TAB_NAME=$1
  COMMAND=$2
  CONTAINER_COMMAND=$3

  if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    if [ -x "$(command -v gnome-terminal)" ]; then
      gnome-terminal \
      --tab --title="$TAB_NAME" --working-directory=`pwd` -- $COMMAND -c \
      "echo '$CONTAINER_COMMAND'; $CONTAINER_COMMAND; exec bash"
    else
      if $PRINT_WARNING; then
          echo -e "\nWARNING: gnome-terminal is the only currently supported way of opening
          multiple tabs/terminals for linux by this script, add support for your setup!"
          PRINT_WARNING=false
      fi
      print_manual_instructions "$COMMAND" "$CONTAINER_COMMAND"
    fi
  elif [[ "$OSTYPE" == "darwin"* ]]; then
    osascript \
        -e "tell application \"Terminal\"" \
        -e "tell application \"System Events\" to keystroke \"t\" using {command down}" \
        -e "do script \"printf '\\\e]1;$TAB_NAME\\\a'; $COMMAND\" in front window" \
        -e "do script \"$CONTAINER_COMMAND\" in front window" \
        -e "end tell" > /dev/null
  else
    if $PRINT_WARNING; then
        echo -e "\nWARNING: The OS '$OSTYPE' is not supported yet for creating tabs to setup
        baserow's dev environemnt, please add support!"
        PRINT_WARNING=false
    fi
    print_manual_instructions "$COMMAND" "$CONTAINER_COMMAND"
  fi
}

docker-compose up -d

new_tab "Backend" \
        "docker exec -it backend bash" \
        "python src/baserow/manage.py runserver 0.0.0.0:8000"

new_tab "Backend celery" \
        "docker exec -it backend bash" \
        "watchmedo auto-restart --directory=./ --pattern=*.py --recursive -- celery -A baserow worker -l INFO"

new_tab "Web frontend" \
        "docker exec -it web-frontend bash" \
        "yarn run dev"

new_tab "Web frontend eslint" \
        "docker exec -it web-frontend bash" \
        "yarn run eslint --fix"
