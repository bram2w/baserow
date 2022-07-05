#!/bin/bash
# Bash strict mode: http://redsymbol.net/articles/unofficial-bash-strict-mode/
set -euo pipefail

# This file is automatically run by Baserow when the plugin is uninstalled.

# Baserow will automatically `pip uninstall` the plugin after this script has been
# called for you so no need to do that in here.

# If you plugin has applied any migrations you should run
# `./baserow migrate {{ cookiecutter.project_module }} zero` here to undo any changes
# made to the database.