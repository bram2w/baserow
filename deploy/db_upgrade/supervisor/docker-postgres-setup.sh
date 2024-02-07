#!/usr/bin/env bash
set -Eeo pipefail

_main() {
    export PGDATA="$DATA_DIR/postgres/"
    export POSTGRES_USER=$DATABASE_USER
    export POSTGRES_PASSWORD=$DATABASE_PASSWORD
    export POSTGRES_DB=$DATABASE_NAME

    chown -R postgres:postgres "$DATA_DIR/"

    if [ "$(id -u)" = '0' ]; then
      # then restart script as postgres user
      echo "Becoming postgres superuser to run setup SQL commands:"
      su postgres -c "${BASH_SOURCE[0]} $*"
    elif [ "$1" == "setup" ]; then
      shift
      ALREADY_SETUP_INDICATOR_FILE="$PGDATA/baserow_db_setup"
      if [ -f "$ALREADY_SETUP_INDICATOR_FILE" ]; then
        echo
        echo 'PostgreSQL Database directory appears to contain a database; Skipping initialization'
        echo

        db_version=$(cat "${PGDATA}/PG_VERSION")

        if [ "$db_version" = "11" ]; then
          echo
          echo 'Upgrading PostgreSQL data directory to version 15 . . .'
          echo

          ./upgrade_postgres.sh
          upgrade_status=$?

          if [ $upgrade_status -ne 0 ]; then
            set +e
            echo
            echo "Upgrading to PostgreSQL 15 failed with exit code $upgrade_status"
            echo
            exit 1
          else
            echo
            echo '. . . PostgreSQL data directory upgrade complete, continuing setup.'
            echo
            # Re-enable 'exit immediately' option.
            set -e
          fi
        else
          echo
          echo 'PostgreSQL data directory is already compatible with PostgreSQL version 15.'
          echo
        fi
      fi
    fi
}

_main "$@"
