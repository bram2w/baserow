#!/bin/bash
# Bash strict mode: http://redsymbol.net/articles/unofficial-bash-strict-mode/
set -euo pipefail

# This script builds the Dockerfile found in the same folder, which is a simple image
# containing the antlr4 parser generator. It then uses this image and runs it with
# the grammar files mounted into to, then generates the appropriate parsers for Baserow
# and finally copies the generated code for those parsers to the correct location.

function realpath()
{
    f=$@
    if [ -d "$f" ]; then
        base=""
        dir="$f"
    else
        base="/$(basename "$f")"
        dir=$(dirname "$f")
    fi
    dir=$(cd "$dir" && /bin/pwd)
    echo "$dir$base"
}


GREEN=$(tput setaf 2)
RED=$(tput setaf 1)
NC=$(tput sgr0) # No Color

# Make sure we run the script in the directory where build.sh is found
# see https://stackoverflow.com/questions/3349105/how-can-i-set-the-current-working-directory-to-the-directory-of-the-script-in-ba
# for the source of this command. The goal is a portable command that cds into the
# current scripts directory.
cd "$(dirname "$(realpath "$0")")";

# Double check the above command worked and we are now indeed in the formula directory
if [ ! -f BaserowFormula.g4 ] || [ ! -f BaserowFormulaLexer.g4 ] || [ ! -d ../backend ] ; then
    echo "${RED}Grammar files or baserow code not found in build scripts directory, cannot continue...${NC}"
    exit 1
fi

echo "Ensuring output folder is clean..."
rm out/ -rf || true

# Build the antlr build image and run it as the current user so the generated files
# are owned by the user and not root.
USER_ID="$(id -u "$USER")"
GROUP_ID="$(id -g "$USER")"

echo "Building antlr4 build image and generating parsers, might take a while..."
docker run -it --rm \
    -v "$(pwd)":/workspace/src \
    -u "$USER_ID":"$GROUP_ID" \
    "$(docker build -q --build-arg UID="$USER_ID" --build-arg GID="$GROUP_ID" . )" sh -c "
        cd src
        java -jar ../antlr.jar -Dlanguage=JavaScript -o out/frontend_parser -visitor -listener BaserowFormulaLexer.g4 BaserowFormula.g4
        java -jar ../antlr.jar -Dlanguage=Python3 -o out/backend_parser -visitor -listener BaserowFormulaLexer.g4 BaserowFormula.g4
    "

echo "Copying the new generated parsers into Baserow's source code overwriting the old ones..."
FRONTEND_OUTPUT_DIR=./../web-frontend/modules/database/formula/parser/generated/
mkdir -p $FRONTEND_OUTPUT_DIR
# Delete all old parser files already in the source code to ensure we are getting a
# fresh clean build
rm -f "$FRONTEND_OUTPUT_DIR"BaserowFormula*
cp out/frontend_parser/* $FRONTEND_OUTPUT_DIR

BACKEND_OUTPUT_DIR=./../backend/src/baserow/contrib/database/formula/parser/generated/
mkdir -p $BACKEND_OUTPUT_DIR
rm -f "$BACKEND_OUTPUT_DIR"BaserowFormula*
cp out/backend_parser/* $BACKEND_OUTPUT_DIR
touch "$BACKEND_OUTPUT_DIR"__init__.py

echo "Moving tokens next to grammar files.."
# Place the generated tokens next to the grammar files also so IDE plugins can use them
# to show more details about the grammar files themselves.
cp out/backend_parser/*.tokens .

echo "Cleaning up out folder..."
rm -f out/backend_parser/*
rm -f out/frontend_parser/*
rmdir out/backend_parser
rmdir out/frontend_parser
rmdir out

echo "${GREEN}Build successfully finished!${NC}"
