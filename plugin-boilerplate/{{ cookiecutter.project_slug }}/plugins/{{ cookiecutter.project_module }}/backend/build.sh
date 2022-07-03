#!/bin/bash
# Bash strict mode: http://redsymbol.net/articles/unofficial-bash-strict-mode/
set -euo pipefail

# This file is automatically run by Baserow when the plugin is built into a Dockerfile.
# It will also be called when building the plugin in an existing container. You should
# only perform build steps in this script.

# Any install steps that will modify things in Baserow's data volume should instead
# be done in the runtime_setup.sh script next to this one. For example running some
# SQL against the embedded postgres database should not be done in this script as it
# makes no sense to do that in a Dockerfile build.

# Baserow will automatically install this python module for you so you should not
# repeat any python dependency installation steps here.

# Instead this file is ideal for any other installation custom steps here required by
# your plugin. For example installing a postgres extension used by your plugin.
