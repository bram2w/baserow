ARG FROM_IMAGE=baserow/baserow:1.8.2
# This is pinned as version pinning is done by the CI setting FROM_IMAGE.
# hadolint ignore=DL3006
FROM $FROM_IMAGE as image_base

RUN apt-get remove -y postgresql postgresql-contrib
# We need to do this at build time as cloudron enforces a readonly filesystem.
RUN mv /baserow/supervisor/includes/disabled/embedded-redis.conf /baserow/supervisor/includes/enabled/embedded-redis.conf

COPY deploy/cloudron/cloudron_env.sh /baserow/supervisor/env/cloudron_env.sh
