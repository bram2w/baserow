ARG FROM_IMAGE=baserow/baserow:1.8.2
# This is pinned as version pinning is done by the CI setting FROM_IMAGE.
# hadolint ignore=DL3006
FROM $FROM_IMAGE as image_base

RUN apt-get remove -y postgresql postgresql-contrib redis-server

ENV DATA_DIR=/baserow/data
ENV DATA_DIR_ALREADY_SETUP=yes
ENV DOCKER_USER=www-data
# We have to build the data dir in the docker image as Caddy does not allow it in their
# runtime filesystem. We chown to their www-data user's uid and gid at the end.
RUN mkdir -p "$DATA_DIR" && \
    mkdir -p "$DATA_DIR"/caddy && \
    mkdir -p "$DATA_DIR"/media && \
    mkdir -p "$DATA_DIR"/env && \
    mkdir -p "$DATA_DIR"/backups && \
    chown -R 33:33 "$DATA_DIR"

COPY deploy/heroku/heroku_env.sh /baserow/supervisor/env/heroku_env.sh

# Reset Entrypoint due to a bug in heroku, always attaching `/bin/sh -c` to the command
# that's run. This causes the end-command to be `/bin/sh -c ...` - which doesn't work.
ENTRYPOINT /bin/bash