#!/usr/bin/env bash
set -Eeo pipefail

# Sets up and starts Baserow and all of its required services using supervisord.

# Use https://manytools.org/hacker-tools/ascii-banner/ and the font ANSI Banner / Wide / Wide to generate
cat << EOF
=========================================================================================

██████╗  █████╗ ███████╗███████╗██████╗  ██████╗ ██╗    ██╗     ██╗    █████╗    ██████╗
██╔══██╗██╔══██╗██╔════╝██╔════╝██╔══██╗██╔═══██╗██║    ██║    ███║   ██╔══██╗   ╚════██╗
██████╔╝███████║███████╗█████╗  ██████╔╝██║   ██║██║ █╗ ██║    ╚██║   ╚█████╔╝    █████╔╝
██╔══██╗██╔══██║╚════██║██╔══╝  ██╔══██╗██║   ██║██║███╗██║     ██║   ██╔══██╗   ██╔═══╝
██████╔╝██║  ██║███████║███████╗██║  ██║╚██████╔╝╚███╔███╔╝     ██║██╗╚█████╔╝██╗███████╗
╚═════╝ ╚═╝  ╚═╝╚══════╝╚══════╝╚═╝  ╚═╝ ╚═════╝  ╚══╝╚══╝      ╚═╝╚═╝ ╚════╝ ╚═╝╚══════╝

=========================================================================================

This is the Baserow all in one Docker image. By default it runs all Baserow services
within a single container.

=== Customization ==

======== USING AN EXTERNAL POSTGRESQL =======

Set DATABASE_HOST, DATABASE_PASSWORD, DATABASE_USER to configure Baserow to use an
external postgres database instead of using its own internal one.

======== USING AN EXTERNAL REDIS =======

Set REDIS_HOST to configure Baserow to use an external redis instead of using its own
internal one.

======== SETTING BASEROW_PUBLIC_URLS AND AUTOMATIC HTTPS =========

Set BASEROW_PUBLIC_URLS if you want Baserow to be available at a configured domain name. Internally
Baserow is using a caddy reverse proxy which will automatically provision SSL
certificates if BASEROW_PUBLIC_URLS is publicly accessible by certbot. For this to work you must
ensure:

* You are running this docker container with ports 80 and 443 exposed and bound ( -p 80:80 -p 443:443)
* You are running this docker container with the BASEROW_PUBLIC_URLS env variable set (-e BASEROW_PUBLIC_URLS=www.yourbaserow.com)
* Your domain's A/AAAA records point to your server
* Ports 80 and 443 are open externally

See https://caddyserver.com/docs/automatic-https for more info

======== FOR MORE HELP ========

For help, feedback and suggestions please post at https://community.baserow.io

TODO
1. Ensure BASEROW_PUBLIC_URLS variable + all the others make sense
2. Provide a better way of managing secrets
   -> postgres password
   -> django secret key
3. Cleanup docs
4. Warn if running in local mode and potentially exposed to the internet.
EOF

startup_echo(){
  ./baserow/supervisor/wrapper.sh GREEN STARTUP echo -e "\e[32m$*\e[0m"
}

# ========================
# = SETUP BLANK INITIAL EMBEDDED DATABASE IF TURNED ON
# ========================

SUPERVISOR_DISABLED_CONF_DIR=/baserow/supervisor/includes/disabled
SUPERVISOR_ENABLED_CONF_DIR=/baserow/supervisor/includes/enabled

if [[ "$DATABASE_HOST" == "localhost" && -z "${DATABASE_URL:-}" ]]; then
  startup_echo "Running first time setup of embedded baserow database."

  # Update the postgres config to point at the DATA_DIR which must be done here as
  # DATA_DIR can change at runtime.
  sed -i "s;/var/lib/postgresql/$POSTGRES_VERSION/main;$DATA_DIR/postgres;g" "$POSTGRES_LOCATION"/postgresql.conf
  chown postgres:postgres "$POSTGRES_LOCATION"/postgresql.conf

  # Setup an empty baserow database with the provided user and password.
  PGDATA="$DATA_DIR/postgres/" \
    POSTGRES_USER=$DATABASE_USER \
    POSTGRES_PASSWORD=$DATABASE_PASSWORD \
    POSTGRES_DB=$DATABASE_NAME \
    ./baserow/supervisor/wrapper.sh GREEN POSTGRES_INIT ./baserow/supervisor/docker-postgres-setup.sh

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
if [[ "$BASEROW_PUBLIC_URLS" == "http://localhost"* ]]; then
  startup_echo "No BASEROW_PUBLIC_URLS environment variable provided. Starting baserow locally at http://localhost without automatic https."
else
  startup_echo "Starting Baserow using addresses $BASEROW_PUBLIC_URLS, if any are https automatically Caddy will attempt to setup HTTPS automatically."
fi

# ========================
# = STARTUP SUPERVISOR
# ========================
startup_echo "Starting all Baserow processes:"
exec /usr/bin/supervisord --configuration "${SUPERVISOR_CONF:-/baserow/supervisor/supervisor.conf}"
