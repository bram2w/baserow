#!/bin/bash
# Bash strict mode: http://redsymbol.net/articles/unofficial-bash-strict-mode/
set -euo pipefail


tabname() {
  printf "\e]1;$1\a"
}

RED=$(tput setaf 1)
GREEN=$(tput setaf 2)
YELLOW=$(tput setaf 3)
NC=$(tput sgr0) # No Color

print_manual_instructions(){
  COMMAND=$1
  echo -e "\nTo inspect the now running dev environment open a new tab/terminal and run:"
  echo "    $COMMAND"
}

PRINT_WARNING=true
new_tab() {
  TAB_NAME=$1
  COMMAND=$2

  if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    if [ -x "$(command -v gnome-terminal)" ]; then
      gnome-terminal \
      --tab --title="$TAB_NAME" --working-directory="$(pwd)" -- /bin/bash -c "$COMMAND"
    else
      if $PRINT_WARNING; then
          echo -e "\n${YELLOW}./dev.sh WARNING${NC}: gnome-terminal is the only currently supported way of opening
          multiple tabs/terminals for linux by this script, add support for your setup!"
          PRINT_WARNING=false
      fi
      print_manual_instructions "$COMMAND"
    fi
  elif [[ "$OSTYPE" == "darwin"* ]]; then
    osascript \
        -e "tell application \"Terminal\"" \
        -e "tell application \"System Events\" to keystroke \"t\" using {command down}" \
        -e "do script \"printf '\\\e]1;$TAB_NAME\\\a'; $COMMAND\" in front window" \
        -e "end tell" > /dev/null
  else
    if $PRINT_WARNING; then
        echo -e "\n${WARNING}./dev.sh WARNING${NC}: The OS '$OSTYPE' is not supported yet for creating tabs to setup
        baserow's dev environment, please add support!"
        PRINT_WARNING=false
    fi
    print_manual_instructions "$COMMAND"
  fi
}

show_help() {
    echo """
./dev.sh starts the baserow development environment and by default attempts to
open terminal tabs which are attached to the running dev containers.

Usage: ./dev.sh [optional start dev commands] [optional docker-compose up commands]

The ./dev.sh Commands are:
restart         : Stop the dev environment first before relaunching.
down            : Down the dev environment and don't up after.
kill            : Kill the dev environment and don't up after.
build_only      : Build the dev environment and don't up after.
dont_migrate    : Disable automatic database migration on baserow startup.
dont_sync       : Disable automatic template sync on baserow startup.
dont_attach     : Don't attach to the running dev containers after starting them.
ignore_ownership: Don't exit if there are files in the repo owned by a different user.
help            : Show this message.
"""
}

dont_attach=false
down=false
kill=false
build=false
run=false
up=true
migrate=true
sync_templates=true
exit_if_other_owners_found=true
delete_db_volume=false
while true; do
case "${1:-noneleft}" in
    dont_migrate)
        echo "./dev.sh: Automatic migration on startup has been disabled."
        shift
        migrate=false
    ;;
    dont_sync)
        echo "./dev.sh: Automatic template syncing on startup has been disabled."
        shift
        sync_templates=false
    ;;
    dont_attach)
        echo "./dev.sh: Configured to not attach to running dev containers."
        shift
        dont_attach=true
    ;;
    restart)
        echo "./dev.sh: Restarting Dev Environment"
        shift
        down=true
        up=true
    ;;
    down)
        echo "./dev.sh: Stopping Dev Environment"
        shift
        up=false
        down=true
    ;;
    kill)
        echo "./dev.sh: Killing Dev Environment"
        shift
        up=false
        kill=true
    ;;
    run)
        echo "./dev.sh: docker-compose running the provided commands"
        shift
        up=false
        dont_attach=true
        run=true
    ;;
    build_only)
        echo "./dev.sh: Only Building Dev Environment (use 'up --build' instead to
        rebuild and up)"
        shift
        build=true
        up=false
    ;;
    restart_wipe)
        echo "./dev.sh: Restarting Dev Env and Wiping Database"
        shift
        down=true
        up=true
        delete_db_volume=true
    ;;
    ignore_ownership)
        echo "./dev.sh: Continuing if files in repo are not owned by $USER."
        shift
        exit_if_other_owners_found=false
    ;;
    help)
        show_help
        exit 0
    ;;
    *)
        break
    ;;
esac
done

OWNERS=$(find . ! -user "$USER")

if [[ $OWNERS ]]; then
if [[ "$exit_if_other_owners_found" = true ]]; then
echo "${RED}./dev.sh ERROR${NC}: Files not owned by your current user: $USER found in this repo.
This will cause file permission errors when Baserow starts up.

They are probably build files created by the old Baserow Docker images owned by root.
Run the following command to show which files are causing this:
  find . ! -user $USER

Please run the following command to fix file permissions in this repository before using ./dev.sh:
  ${GREEN}sudo chown $USER -R .${NC}

OR you can ignore this check by running with the ignore_ownership arg:
  ${YELLOW}./dev.sh ignore_ownership ...${NC}"
exit;
else

echo "${YELLOW}./dev.sh WARNING${NC}: Files not owned by your current user: $USER found in this repo.
Continuing as 'ignore_ownership' argument provided."
fi

fi

# Set various env variables to sensible defaults if they have not already been set by
# the user.
if [[ -z "${UID:-}" ]]; then
UID=$(id -u)
export UID
fi

if [[ -z "${GID:-}" ]]; then
export GID
GID=$(id -g)
fi


if [[ -z "${MIGRATE_ON_STARTUP:-}" ]]; then
if [ "$migrate" = true ] ; then
export MIGRATE_ON_STARTUP="true"
else
# Because of the defaults set in the docker-compose file we need to explicitly turn
# this off as just not setting it will get the default "true" value.
export MIGRATE_ON_STARTUP="false"
fi
else
  echo "./dev.sh Using the already set value for the env variable MIGRATE_ON_STARTUP = $MIGRATE_ON_STARTUP"
fi

if [[ -z "${SYNC_TEMPLATES_ON_STARTUP:-}" ]]; then
if [ "$sync_templates" = true ] ; then
export SYNC_TEMPLATES_ON_STARTUP="true"
else
# Because of the defaults set in the docker-compose file we need to explicitly turn
# this off as just not setting it will get the default "true" value.
export SYNC_TEMPLATES_ON_STARTUP="false"
fi
else
  echo "./dev.sh Using the already set value for the env variable SYNC_TEMPLATES_ON_STARTUP = $SYNC_TEMPLATES_ON_STARTUP"
fi

echo "./dev.sh running docker-compose commands:
------------------------------------------------
"

if [ "$down" = true ] ; then
# Remove the containers and remove the anonymous volumes for cleanliness sake.
docker-compose -f docker-compose.yml -f docker-compose.dev.yml rm -s -v -f
fi

if [ "$kill" = true ] ; then
docker-compose -f docker-compose.yml -f docker-compose.dev.yml kill
fi

if [ "$build" = true ] ; then
docker-compose -f docker-compose.yml -f docker-compose.dev.yml build "$@"
fi

if [ "$delete_db_volume" = true ] ; then
  docker volume rm baserow_pgdata
fi

if [ "$up" = true ] ; then
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d "$@"
fi

if [ "$run" = true ] ; then
docker-compose -f docker-compose.yml -f docker-compose.dev.yml run "$@"
fi

if [ "$dont_attach" != true ] && [ "$up" = true ] ; then
  new_tab "Backend" \
          "docker logs backend && docker attach backend"

  new_tab "Backend celery" \
          "docker logs celery && docker attach celery"

  new_tab "Backend celery export worker" \
          "docker logs celery-export-worker && docker attach celery-export-worker"

  new_tab "Backend celery beat worker" \
          "docker logs celery-beat-worker && docker attach celery-beat-worker"

  new_tab "Web frontend" \
          "docker logs web-frontend && docker attach web-frontend"

  new_tab "Web frontend lint" \
          "docker exec -it web-frontend /bin/bash /baserow/web-frontend/docker/docker-entrypoint.sh lint-fix"
fi
