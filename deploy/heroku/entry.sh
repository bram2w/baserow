#!/bin/bash

set -eu

sed -i 's/PORT/'"$PORT"'/g' /baserow/nginx.conf
export BASEROW_PUBLIC_URL=${BASEROW_PUBLIC_URL:-https://$HEROKU_APP_NAME.herokuapp.com}
export REDIS_URL=${REDIS_TLS_URL:-$REDIS_URL}
