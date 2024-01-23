#!/usr/bin/env bash
set -Eeo pipefail

# Sets up and starts Baserow and all of its required services using supervisord.

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
cat /baserow/supervisor/STARTUP_README.md

startup_echo(){
  /baserow/supervisor/wrapper.sh GREEN STARTUP echo -e "\e[32m$*\e[0m"
}

# ========================
# = SETUP BLANK INITIAL EMBEDDED DATABASE IF TURNED ON
# ========================

SUPERVISOR_DISABLED_CONF_DIR=/baserow/supervisor/includes/disabled
SUPERVISOR_ENABLED_CONF_DIR=/baserow/supervisor/includes/enabled

if [[ "$DATABASE_HOST" == "localhost" && -z "${DATABASE_URL:-}" ]]; then
  startup_echo "Running setup of embedded baserow database."

  # Update the postgres config to point at the DATA_DIR which must be done here as
  # DATA_DIR can change at runtime.
  sed -i "s;/var/lib/postgresql/$POSTGRES_VERSION/main;$DATA_DIR/postgres;g" "$POSTGRES_LOCATION"/postgresql.conf
  chown postgres:postgres "$POSTGRES_LOCATION"/postgresql.conf

  # Setup an empty baserow database with the provided user and password.
  ./baserow/supervisor/wrapper.sh GREEN POSTGRES_INIT ./baserow/supervisor/docker-postgres-setup.sh setup

  _use_postgresql15() {
    export POSTGRES_VERSION=15
    export POSTGRES_LOCATION="/baserow/data/postgres"
  }

  ALREADY_UPGRADED_INDICATOR_FILE="$PGDATA/baserow_db_upgrade"
  if [ -f "$ALREADY_UPGRADED_INDICATOR_FILE" ]; then
    echo
    echo 'PostgreSQL Database already upgraded to version 15; Skipping upgrade.'
    echo
    _use_postgresql15
  else
    #running as root:
    set +e  # Disable 'exit immediately' option

    ./upgrade_postgres.sh

    upgrade_status=$?
    #TODO: if script completes successfully, here, remove the old PostgresSQL binaries?

    if [ $upgrade_status -ne 0 ]; then
      startup_echo "Upgrading to PostgreSQL 15 failed with exit code $upgrade_status"
    else
      #All went fine with the upgrade, so use the new PostgreSQL 15 in subsequent steps, in the
      #Dockerfile we have these set to PostgreSQL 11, these are picekd up by supervisor
      #during startup:
      _use_postgresql15
      touch "$ALREADY_UPGRADED_INDICATOR_FILE"
      startup_echo "upgrade_postgres.sh succeeded with exit code $upgrade_status"
    fi
    # Re-enable 'exit immediately' option.
    # TODO: check with 'set -Eeo pipefail' at the top:
    set -e
  fi

  # Enable the embedded postgres by moving it into the directory from which supervisor
  # includes all .conf files it finds.
  if [ ! -f "$SUPERVISOR_ENABLED_CONF_DIR/embedded-postgres.conf" ]; then
    mv "$SUPERVISOR_DISABLED_CONF_DIR/embedded-postgres.conf" "$SUPERVISOR_ENABLED_CONF_DIR/embedded-postgres.conf"
  fi
elif [ -f "$SUPERVISOR_ENABLED_CONF_DIR/embedded-postgres.conf" ]; then
  # Disable the embedded postgres if somehow the conf is in the enabled folder
  mv "$SUPERVISOR_ENABLED_CONF_DIR/embedded-postgres.conf" "$SUPERVISOR_DISABLED_CONF_DIR/embedded-postgres.conf" 2>/dev/null || true
fi

# ========================
# = SETUP EMBEDDED REDIS IF TURNED ON
# ========================
if [[ "$REDIS_HOST" == "localhost" && -z "${REDIS_URL:-}" ]]; then
  # Enable the embedded redis by moving it into the directory from which supervisor
  # includes all .conf files it finds.
  if [ ! -f "$SUPERVISOR_ENABLED_CONF_DIR/embedded-redis.conf" ]; then
    mv "$SUPERVISOR_DISABLED_CONF_DIR/embedded-redis.conf" "$SUPERVISOR_ENABLED_CONF_DIR/embedded-redis.conf"
  fi
elif [ -f "$SUPERVISOR_ENABLED_CONF_DIR/embedded-redis.conf" ]; then
  # Disable the embedded redis if somehow the conf is in the enabled folder
  mv "$SUPERVISOR_ENABLED_CONF_DIR/embedded-redis.conf" "$SUPERVISOR_DISABLED_CONF_DIR/embedded-redis.conf" 2>/dev/null || true
fi

# ========================
# = LOG ABOUT URL
# ========================
if [[ "$BASEROW_PUBLIC_URL" == "http://localhost"* ]]; then
  startup_echo "No BASEROW_PUBLIC_URL environment variable provided. Starting baserow locally at http://localhost without automatic https."
else
  startup_echo "Starting Baserow using addresses $BASEROW_PUBLIC_URL, if any are https automatically Caddy will attempt to setup HTTPS automatically."
fi

# ========================
# = INSTALL PLUGINS
# ========================

source /baserow/plugins/utils.sh
startup_plugin_setup

# ========================
# = STARTUP SUPERVISOR
# ========================
startup_echo "Starting all Baserow processes:"
exec /usr/bin/supervisord --configuration "${SUPERVISOR_CONF:-/baserow/supervisor/supervisor.conf}"
