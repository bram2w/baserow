#!/bin/bash
# Bash strict mode: http://redsymbol.net/articles/unofficial-bash-strict-mode/
set -euo pipefail


show_help() {
# If you change this please update ./docs/reference/baserow-docker-api.md
    echo """
Usage: docker run [-T] baserow_web-frontend[_dev] COMMAND
Commands
dev      : Start a normal nuxt development server
local    : Start a non-dev prod ready nuxt server
lint     : Run all the linting
lint-fix : Run eslint fix
stylelint: Run stylelint
eslint   : Run eslint
ci-test  : Run ci tests with reporting
bash     : Start a bash shell
help     : Show this message
"""
}


case "$1" in
    dev)
        CMD="yarn run dev"
        echo "$CMD"
        # The below command lets devs attach to this container, press ctrl-c and only
        # the server will stop. Additionally they will be able to use bash history to
        # re-run the containers run server command after they have done what they want.
        exec bash --init-file <(echo "history -s $CMD; $CMD")
    ;;
    local)
      exec yarn run start
    ;;
    lint)
      exec make lint-javascript
    ;;
    lint-fix)
      CMD="yarn run eslint --fix"
      echo "$CMD"
      exec bash --init-file <(echo "history -s $CMD; $CMD")
    ;;
    eslint)
      exec make eslint
    ;;
    stylelint)
      exec make eslint
    ;;
    ci-test)
      exec make ci-test
    ;;
    bash)
      exec /bin/bash "${@:2}"
    ;;
    *)
      show_help
      exit 1
    ;;
esac