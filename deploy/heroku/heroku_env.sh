#!/bin/bash

set -eu

# Heroku is configured with the non-plural version of this variable.
# Default to using it but also allow the user to set BASEROW_PUBLIC_URLS.
BASEROW_PUBLIC_URL=${BASEROW_PUBLIC_URL:-https://$HEROKU_APP_NAME.herokuapp.com, :$PORT}
export BASEROW_PUBLIC_URLS=${BASEROW_PUBLIC_URLS:-$BASEROW_PUBLIC_URL}
# Only listen to the port with caddy to disable its automatic ssl
export BASEROW_CADDY_GLOBAL_CONF="auto_https off"
export REDIS_URL=${REDIS_TLS_URL:-$REDIS_URL}
export DJANGO_SETTINGS_MODULE='baserow.config.settings.heroku'
export BASEROW_RUN_MINIMAL_CELERY=yes
export DISABLE_EMBEDDED_PSQL=yes
export SYNC_TEMPLATES_ON_STARTUP="${SYNC_TEMPLATES_ON_STARTUP:-no}"
# Heroku does not support mounting volumes!
export DISABLE_VOLUME_CHECK=yes

export BASEROW_AMOUNT_OF_WORKERS=${BASEROW_AMOUNT_OF_WORKERS:-1}
export BASEROW_AMOUNT_OF_GUNICORN_WORKERS=${BASEROW_AMOUNT_OF_GUNICORN_WORKERS:-$BASEROW_AMOUNT_OF_WORKERS}

export EMAIL_SMTP="true"
export EMAIL_SMTP_USE_TLS=""
export FROM_EMAIL="no-reply@$MAILGUN_DOMAIN"

export EMAIL_SMTP_HOST=$MAILGUN_SMTP_SERVER
export EMAIL_SMTP_PORT=$MAILGUN_SMTP_PORT
export EMAIL_SMTP_USER=$MAILGUN_SMTP_LOGIN
export EMAIL_SMTP_PASSWORD=$MAILGUN_SMTP_PASSWORD