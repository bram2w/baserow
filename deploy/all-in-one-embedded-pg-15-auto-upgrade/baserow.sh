#!/bin/bash
# Bash strict mode: http://redsymbol.net/articles/unofficial-bash-strict-mode/
set -euo pipefail

# Use https://manytools.org/hacker-tools/ascii-banner/ and the font ANSI Banner / Wide / Wide to generate
cat << EOF
=========================================================================================

██████╗  █████╗ ███████╗███████╗██████╗  ██████╗ ██╗    ██╗
██╔══██╗██╔══██╗██╔════╝██╔════╝██╔══██╗██╔═══██╗██║    ██║
██████╔╝███████║███████╗█████╗  ██████╔╝██║   ██║██║ █╗ ██║
██╔══██╗██╔══██║╚════██║██╔══╝  ██╔══██╗██║   ██║██║███╗██║
██████╔╝██║  ██║███████║███████╗██║  ██║╚██████╔╝╚███╔███╔╝
╚═════╝ ╚═╝  ╚═╝╚══════╝╚══════╝╚═╝  ╚═╝ ╚═════╝  ╚══╝╚══╝

Version 1.22.2

=========================================================================================
EOF

# From https://github.com/docker-library/postgres/blob/master/docker-entrypoint.sh
# usage: file_env VAR [DEFAULT]
#    ie: file_env 'XYZ_DB_PASSWORD' 'example'
# (will allow for "$XYZ_DB_PASSWORD_FILE" to fill in the value of
#  "$XYZ_DB_PASSWORD" from a file, especially for Docker's secrets feature)
file_env() {
	local var="$1"
	local fileVar="${var}_FILE"
	local def="${2:-}"
	if [ "${!var:-}" ] && [ "${!fileVar:-}" ]; then
		echo >&2 "error: both $var and $fileVar are set (but are exclusive)"
		exit 1
	fi
	local val="$def"
	if [ "${!var:-}" ]; then
		val="${!var}"
	elif [ "${!fileVar:-}" ]; then
		val="$(< "${!fileVar}")"
	fi
	export "$var"="$val"
	unset "$fileVar"
}

startup_echo(){
  /baserow/supervisor/wrapper.sh GREEN STARTUP echo -e "\e[32m$*\e[0m"
}

create_secret_env_if_missing(){
  SECRET_FILE="$DATA_DIR/$1"
  if [[ -z "${!2:-}" ]]; then
    startup_echo "Importing $2 secret from $SECRET_FILE"
    # shellcheck disable=SC1090
    source "$SECRET_FILE"
  fi
}

case "$1" in
    start)
      file_env DATABASE_PASSWORD
      create_secret_env_if_missing .pgpass DATABASE_PASSWORD

      export DATABASE_NAME="${DATABASE_NAME:-baserow}"
      export DATABASE_USER="${DATABASE_USER:-baserow}"

      export PGDATA="$DATA_DIR/postgres/"
      export POSTGRES_USER=$DATABASE_USER
      export POSTGRES_PASSWORD=$DATABASE_PASSWORD
      export POSTGRES_DB=$DATABASE_NAME

      chown -R postgres:postgres "$DATA_DIR/"

      # Update the postgres config to point at the DATA_DIR which must be done here as
      # DATA_DIR can change at runtime.
      sed -i "s;/var/lib/postgresql/$POSTGRES_VERSION/main;$DATA_DIR/postgres;g" "$POSTGRES_LOCATION"/postgresql.conf
      chown postgres:postgres "$POSTGRES_LOCATION"/postgresql.conf

      ALREADY_SETUP_INDICATOR_FILE="$PGDATA/baserow_db_setup"
      if [ -f "$ALREADY_SETUP_INDICATOR_FILE" ]; then
        echo
        echo 'PostgreSQL Database directory appears to contain a database; Performing upgrade check.'
        echo

        db_version=$(cat "${PGDATA}/PG_VERSION")

        if [ "$db_version" = "11" ]; then
          echo
          echo 'Upgrading PostgreSQL data directory to version 15 . . .'
          echo

          su postgres -c ./upgrade_postgres.sh
          upgrade_status=$?

          if [ $upgrade_status -ne 0 ]; then
            set +e
            echo
            echo "Upgrading to PostgreSQL 15 failed with exit code $upgrade_status"
            echo
            exit 1
          else
            echo
            echo '. . . PostgreSQL data directory upgrade complete!'
            echo
            exit 0
          fi
        else
          echo
          echo 'PostgreSQL data directory is already compatible with PostgreSQL version 15.'
          echo
          exit 0
        fi
      else
        echo
        echo 'PostgreSQL Database directory does not appear to contain a database;'
        echo
        exit 1
      fi
    ;;
esac
