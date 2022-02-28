ARG FROM_IMAGE=baserow/baserow:1.8.2
# This is pinned as version pinning is done by the CI setting FROM_IMAGE.
# hadolint ignore=DL3006
FROM $FROM_IMAGE as image_base

RUN apt-get remove -y postgresql postgresql-contrib redis-server

COPY deploy/heroku/heroku_env.sh /baserow/supervisor/env/heroku_env.sh

ENTRYPOINT ["/bin/bash"]
CMD ["./baserow.sh", "start"]