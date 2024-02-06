#!/usr/bin/env bash
set -Eeo pipefail

# A simple helper script which loops forever checking the backend and frontend
# healthcheck endpoints. When the services become healthy it informs the user how to
# access them,

baserow_ready() {
    curlf() {
      HTTP_CODE=$(curl --silent -o /dev/null --write-out "%{http_code}" --max-time 10 "$@")
      if [[ ${HTTP_CODE} -lt 200 || ${HTTP_CODE} -gt 299 ]] ; then
        return 22
      fi
      return 0
    }

    if curlf "http://localhost:3000/_health/" && curlf "http://localhost:8000/api/_health/"; then
      return 0
    else
      return 1
    fi
}

wait_for_baserow() {
  until baserow_ready; do
    echo 'Waiting for Baserow to become available, this might take 30+ seconds...'
    sleep 10
  done
  echo "======================================================================="
  echo -e "\e[32mBaserow is now available at ${BASEROW_PUBLIC_URL}\e[0m"
  echo "======================================================================="

  # Now go into warning mode where we loop and inform about changes in health.
  unhealthy=false
  while true
  do
    sleep 20
    if ! baserow_ready; then
      echo -e "\e[32mWARNING: Baserow has become unhealthy.\e[0m"
      unhealthy=true
    elif [ "$unhealthy" = true ]; then
      echo -e "\e[33mBaserow has become healthy.\e[0m"
      unhealthy=false
    fi
  done
}

wait_for_baserow
