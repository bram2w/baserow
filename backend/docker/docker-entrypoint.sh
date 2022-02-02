#!/bin/bash
# Bash strict mode: http://redsymbol.net/articles/unofficial-bash-strict-mode/
set -euo pipefail

# Used by docker-entrypoint.sh to start the dev server
# If not configured you'll receive this: CommandError: "0.0.0.0:" is not a valid port number or address:port pair.
PORT="${PORT:-8000}"
DATABASE_USER="${DATABASE_USER:-postgres}"
DATABASE_HOST="${DATABASE_HOST:-db}"
DATABASE_PORT="${DATABASE_PORT:-5432}"

source "/baserow/venv/bin/activate"

postgres_ready() {
python << END
import sys
import psycopg2
try:
    psycopg2.connect(
        dbname="${DATABASE_NAME}",
        user="${DATABASE_USER}",
        password="${DATABASE_PASSWORD}",
        host="${DATABASE_HOST}",
        port="${DATABASE_PORT}",
    )
except psycopg2.OperationalError:
    sys.exit(-1)
sys.exit(0)
END
}

wait_for_postgres() {
until postgres_ready; do
  >&2 echo 'Waiting for PostgreSQL to become available...'
  sleep 1
done
>&2 echo 'PostgreSQL is available'
}



show_help() {
# If you change this please update ./docs/reference/baserow-docker-api.md
    echo """
Usage: docker run [-T] baserow_backend[_dev] COMMAND
Commands
local           : Start django using a prod ready gunicorn server
dev             : Start a normal Django development server
exec            : Exec a command directly
bash            : Start a bash shell
manage          : Start manage.py
setup           : Runs all setup commands (migrate, update_formulas, sync_templates)
python          : Run a python command
shell           : Start a Django Python shell
celery          : Run celery
celery-dev:     : Run a hot-reloading dev version of celery
lint:           : Run the linting (only available if using dev target)
lint-exit       : Run the linting and exit (only available if using dev target)
test:           : Run the tests (only available if using dev target)
ci-test:        : Run the tests for ci including various reports (dev only)
ci-check-startup: Start up a single gunicorn and timeout after 10 seconds for ci (dev).
help            : Show this message
"""
}

run_setup_commands_if_configured(){
if [ "$MIGRATE_ON_STARTUP" = "true" ] ; then
  echo "python /baserow/backend/src/baserow/manage.py migrate"
  python /baserow/backend/src/baserow/manage.py migrate
fi
if [ "$SYNC_TEMPLATES_ON_STARTUP" = "true" ] ; then
  echo "python /baserow/backend/src/baserow/manage.py sync_templates"
  python /baserow/backend/src/baserow/manage.py sync_templates
fi
}

case "$1" in
    dev)
        wait_for_postgres
        run_setup_commands_if_configured
        echo "Running Development Server on 0.0.0.0:${PORT}"
        echo "Press CTRL-p CTRL-q to close this session without stopping the container."
        CMD="python /baserow/backend/src/baserow/manage.py runserver 0.0.0.0:${PORT}"
        echo "$CMD"
        # The below command lets devs attach to this container, press ctrl-c and only
        # the server will stop. Additionally they will be able to use bash history to
        # re-run the containers run server command after they have done what they want.
        exec bash --init-file <(echo "history -s $CMD; $CMD")
    ;;
    local)
        wait_for_postgres
        run_setup_commands_if_configured
        exec gunicorn --workers=3 -b 0.0.0.0:"${PORT}" -k uvicorn.workers.UvicornWorker baserow.config.asgi:application
    ;;
    exec)
        exec "${@:2}"
    ;;
    bash)
        exec /bin/bash "${@:2}"
    ;;
    manage)
        exec python /baserow/backend/src/baserow/manage.py "${@:2}"
    ;;
    python)
        exec python "${@:2}"
    ;;
    setup)
      echo "python /baserow/backend/src/baserow/manage.py migrate"
      python /baserow/backend/src/baserow/manage.py migrate
      echo "python /baserow/backend/src/baserow/manage.py update_formulas"
      python /baserow/backend/src/baserow/manage.py update_formulas
      echo "python /baserow/backend/src/baserow/manage.py sync_templates"
      python /baserow/backend/src/baserow/manage.py sync_templates
    ;;
    shell)
        exec python /baserow/backend/src/baserow/manage.py shell
    ;;
    lint-shell)
        CMD="make lint-python"
        echo "$CMD"
        exec bash --init-file <(echo "history -s $CMD; $CMD")
    ;;
    lint)
        exec make lint-python
    ;;
    ci-test)
        exec make ci-test-python PYTEST_SPLITS="${PYTEST_SPLITS:-1}" PYTEST_SPLIT_GROUP="${PYTEST_SPLIT_GROUP:-1}"
    ;;
    ci-check-startup)
        exec make ci-check-startup-python
    ;;
    celery)
        exec celery -A baserow "${@:2}"
    ;;
    celery-dev)
        # Ensure we watch all possible python source code locations for changes.
        directory_args=''
        for i in $(echo "$PYTHONPATH" | tr ":" "\n")
        do
          directory_args="$directory_args -d=$i"
        done

        CMD="watchmedo auto-restart $directory_args --pattern=*.py --recursive -- celery -A baserow ${*:2}"
        echo "$CMD"
        # The below command lets devs attach to this container, press ctrl-c and only
        # the server will stop. Additionally they will be able to use bash history to
        # re-run the containers run server command after they have done what they want.
        exec bash --init-file <(echo "history -s $CMD; $CMD")
    ;;
    *)
        echo "${@:2}"
        show_help
        exit 1
    ;;
esac
