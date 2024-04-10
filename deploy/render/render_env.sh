#!/bin/bash

set -euo pipefail

export BASEROW_PUBLIC_URL=$RENDER_EXTERNAL_URL
export BASEROW_CADDY_ADDRESSES=":$PORT"
export REDIS_URL=${REDIS_TLS_URL:-$REDIS_URL}
export DJANGO_SETTINGS_MODULE='baserow.config.settings.heroku'
export BASEROW_RUN_MINIMAL=yes
export DISABLE_EMBEDDED_PSQL=yes
export DISABLE_EMBEDDED_REDIS=yes
export BASEROW_TRIGGER_SYNC_TEMPLATES_AFTER_MIGRATION=${BASEROW_TRIGGER_SYNC_TEMPLATES_AFTER_MIGRATION:-true}
export MIGRATE_ON_STARTUP="${MIGRATE_ON_STARTUP:-}"
# Render does not support mounting volumes!
export DISABLE_VOLUME_CHECK=yes

export BASEROW_AMOUNT_OF_WORKERS=${BASEROW_AMOUNT_OF_WORKERS:-1}
export BASEROW_AMOUNT_OF_GUNICORN_WORKERS=${BASEROW_AMOUNT_OF_GUNICORN_WORKERS:-$BASEROW_AMOUNT_OF_WORKERS}

# Disable auto https redirect because otherwise it will make Caddy bind on port 80.
# This is not allowed by Render, and will prevent it from starting.
export BASEROW_CADDY_GLOBAL_CONF="auto_https disable_redirects
http_port $PORT"

export EMAIL_SMTP="false"
# Render generates a random user who runs this container, set DOCKER_USER to that user
# so we can setup the DATA_DIR.
DOCKER_USER=$(whoami)
export DOCKER_USER

# We must run the caddy user as the docker user to prevent supervisord errors
export BASEROW_CADDY_USER="${BASEROW_CADDY_USER:-$DOCKER_USER}"
