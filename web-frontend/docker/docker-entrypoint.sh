#!/bin/bash
# Bash strict mode: http://redsymbol.net/articles/unofficial-bash-strict-mode/
set -euo pipefail

BASEROW_WEBFRONTEND_PORT="${BASEROW_WEBFRONTEND_PORT:-3000}"

show_help() {
    echo """
The available Baserow web-frontend related commands and services are shown below:

COMMANDS:
nuxt-dev   : Start a normal nuxt development server
nuxt       : Start a non-dev prod ready nuxt server
nuxt-local : Start a non-dev prod ready nuxt server using the preset local config
bash     : Start a bash shell

DEV COMMANDS:
lint     : Run all the linting
lint-fix : Run eslint fix
stylelint: Run stylelint
eslint   : Run eslint
test     : Run jest tests
ci-test  : Run ci tests with reporting
help     : Show this message
"""
}

# Lets devs attach to this container running the passed command, press ctrl-c and only
# the command will stop. Additionally they will be able to use bash history to
# re-run the containers command after they have done what they want.
attachable_exec(){
    echo "$@"
    exec bash --init-file <(echo "history -s $*; $*")
}

if [[ -z "${1:-}" ]]; then
  echo "Must provide arguments to docker-entrypoint.sh"
  show_help
  exit 1
fi


case "$1" in
    nuxt-dev)
        attachable_exec yarn run dev
    ;;
    nuxt)
      exec ./node_modules/.bin/nuxt start --hostname "${BASEROW_WEBFRONTEND_BIND_ADDRESS:-0.0.0.0}" --port "$BASEROW_WEBFRONTEND_PORT" "${@:2}"
    ;;
    nuxt-local)
      exec ./node_modules/.bin/nuxt start --hostname "${BASEROW_WEBFRONTEND_BIND_ADDRESS:-0.0.0.0}" --port "$BASEROW_WEBFRONTEND_PORT" --config-file ./config/nuxt.config.local.js "${@:2}"
    ;;
    lint)
      exec make lint-javascript
    ;;
    lint-fix)
      attachable_exec yarn run eslint --fix
    ;;
    eslint)
      exec make eslint
    ;;
    stylelint)
      exec make eslint
    ;;
    test)
      exec make jest
    ;;
    ci-test)
      exec make ci-test-javascript
    ;;
    bash)
      exec /bin/bash -c "${@:2}"
    ;;
    *)
      echo "Command given was $*"
      show_help
      exit 1
    ;;
esac
