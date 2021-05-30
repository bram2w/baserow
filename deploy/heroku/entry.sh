#!/bin/bash

set -eu

sed -i 's/$PORT/'"$PORT"'/g' /etc/nginx/sites-enabled/nginx.conf
export BASEROW_PUBLIC_URL=${BASEROW_PUBLIC_URL:-https://$HEROKU_APP_NAME.herokuapp.com}
/usr/bin/supervisord --configuration /etc/supervisor/conf.d/supervisor.conf
