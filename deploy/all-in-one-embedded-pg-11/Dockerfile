ARG FROM_IMAGE=baserow:latest
#FIXME:
#ARG FROM_IMAGE=baserow/baserow:1.22.2

# This is pinned as version pinning is done by the CI setting FROM_IMAGE.
# hadolint ignore=DL3006
FROM $FROM_IMAGE as image_base

# Remove PostgreSQL 15
RUN DEBIAN_FRONTEND=noninteractive apt-get remove -y --purge postgresql-15 postgresql-client-15 && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /var/lib/postgresql/15 /etc/postgresql/15

# Add the PostgreSQL 11 repository and install PostgreSQL 11
RUN echo "deb http://apt.postgresql.org/pub/repos/apt $(. /etc/os-release; echo $VERSION_CODENAME)-pgdg main" > /etc/apt/sources.list.d/pgdg.list && \
    curl -fsSL https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add - && \
    apt-get update && \
    apt-get install --no-install-recommends -y postgresql-11 postgresql-client-11 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Adjust PostgreSQL configuration to use the correct version
ENV POSTGRES_VERSION=11
ENV POSTGRES_LOCATION=/etc/postgresql/11/main

COPY --chown=$UID:$GID deploy/all-in-one-embedded-pg-11/supervisor/ /baserow/supervisor
