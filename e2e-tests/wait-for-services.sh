#!/usr/bin/env bash
set -Eeo pipefail

# This script waits 60 seconds by default for the backend and web-frontend services
# to become healthy.

baserow_ready() {
    curlf() {
      HTTP_CODE=$(curl --silent -o /dev/null --write-out "%{http_code}" --max-time 10 "$@")
      if [[ ${HTTP_CODE} -lt 200 || ${HTTP_CODE} -gt 299 ]] ; then
        return 22
      fi
      return 0
    }

    if curlf "${PUBLIC_WEB_FRONTEND_URL:-http://web-frontend:3000}/_health/" && curlf "${PUBLIC_BACKEND_URL:-http://backend:8000}/_health/"; then
      return 0
    else
      return 1
    fi
}

for _ in $(seq 1 "${BASEROW_E2E_STARTUP_MAX_WAIT_TIME_SECONDS:-60}")
do
  echo 'Waiting for backend and web-frontend to become available'
  if baserow_ready; then
    exit 0
  fi
  sleep 1
done
echo 'E2E services failed to startup in time, crashing the test.'
exit 1
