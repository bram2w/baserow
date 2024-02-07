#!/usr/bin/env bash
set -Eeo pipefail

# Sets up and starts Baserow and all of its required services using supervisord.

# Use https://manytools.org/hacker-tools/ascii-banner/ and the font ANSI Banner / Wide / Wide to generate
cat << EOF
=========================================================================================

██████╗  █████╗ ███████╗███████╗██████╗  ██████╗ ██╗    ██╗
██╔══██╗██╔══██╗██╔════╝██╔════╝██╔══██╗██╔═══██╗██║    ██║
██████╔╝███████║███████╗█████╗  ██████╔╝██║   ██║██║ █╗ ██║
██╔══██╗██╔══██║╚════██║██╔══╝  ██╔══██╗██║   ██║██║███╗██║
██████╔╝██║  ██║███████║███████╗██║  ██║╚██████╔╝╚███╔███╔╝
╚═════╝ ╚═╝  ╚═╝╚══════╝╚══════╝╚═╝  ╚═╝ ╚═════╝  ╚══╝╚══╝

Version 1.22.2

=========================================================================================
EOF

# Update the postgres config to point at the DATA_DIR which must be done here as
# DATA_DIR can change at runtime.
sed -i "s;/var/lib/postgresql/$POSTGRES_VERSION/main;$DATA_DIR/postgres;g" "$POSTGRES_LOCATION"/postgresql.conf
chown postgres:postgres "$POSTGRES_LOCATION"/postgresql.conf

# Setup an empty baserow database with the provided user and password.
./baserow/supervisor/wrapper.sh GREEN POSTGRES_INIT ./baserow/supervisor/docker-postgres-setup.sh setup
