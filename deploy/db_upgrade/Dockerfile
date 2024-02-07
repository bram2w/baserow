# hadolint ignore=DL3006
FROM debian:bullseye-slim as base

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

ARG UID
ENV UID=${UID:-9999}
ARG GID
ENV GID=${GID:-9999}
ARG DOCKER_USER
ENV DOCKER_USER=${DOCKER_USER:-baserow_docker_user}

ENV DATA_DIR=/baserow/data
ENV BASEROW_PLUGIN_DIR=$DATA_DIR/plugins
ENV POSTGRES_VERSION=11
ENV TARGET_POSTGRES_VERSION=15
ENV NODE_MAJOR=18
ENV POSTGRES_LOCATION=/etc/postgresql/15/main
ENV BASEROW_IMAGE_TYPE="all-in-one"

# ========================
# = INSTALL DEPENDENCIES
# ========================
RUN apt-get update && \
    apt-get upgrade -y && \
    DEBIAN_FRONTEND=noninteractive TZ=Etc/UTC apt-get install --no-install-recommends -y \
    make supervisor curl gnupg2 \
    build-essential \
    lsb-release \
    ca-certificates \
    && \
    # Postgresql repository has to be added manually to get pre-13 versions.
    echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list && \
    curl -fsSL https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add - \
    && \
    # Install the correct version of postgresql and the remaining packages
    apt-get update && \
    apt-get install --no-install-recommends -y \
    #Existing PostgreSQL version:
    postgresql-$POSTGRES_VERSION \
    postgresql-client-$POSTGRES_VERSION \
    #Target PostgreSQL version:
    postgresql-$TARGET_POSTGRES_VERSION \
    postgresql-client-$TARGET_POSTGRES_VERSION \
    gawk && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* &&  \
    # ========================
    # Setup Users
    # ========================
    ( groupadd -g "$GID" baserow_docker_group || true ) && \
    ( useradd --shell /bin/bash -u $UID -g "$GID" -o -c "" -m "$DOCKER_USER" -l || true) && \
    usermod -a -G tty "$DOCKER_USER"

# ========================
# = DB upgrade stage
# ========================
COPY --chown=$UID:$GID deploy/db_upgrade/supervisor/ /baserow/supervisor

COPY upgrade_postgres.sh /upgrade_postgres.sh
RUN chmod +x /upgrade_postgres.sh

COPY --chown=$UID:$GID deploy/db_upgrade/baserow.sh /baserow.sh
ENTRYPOINT ["/baserow.sh"]
CMD ["start"]
EXPOSE 80
