#!/bin/bash

set -eu

if [[ ! -f /app/data/.secret ]]; then
    echo "export SECRET_KEY=$(tr -dc 'a-z0-9' < /dev/urandom | head -c50)" > /app/data/.secret
fi
source /app/data/.secret

mkdir -p /app/data/redis

echo "==> Executing database migrations"
/app/code/env/bin/python /app/code/baserow/backend/src/baserow/manage.py migrate --settings=cloudron.settings

echo "==> Syncing templates"
/app/code/env/bin/python /app/code/baserow/backend/src/baserow/manage.py sync_templates --settings=cloudron.settings

echo "==> Updating formulas"
/app/code/env/bin/python /app/code/baserow/backend/src/baserow/manage.py update_formulas --settings=cloudron.settings

chown -R cloudron:cloudron /app/data

echo "==> Starting"
exec /usr/bin/supervisord --configuration /etc/supervisor/conf.d/supervisor.conf
