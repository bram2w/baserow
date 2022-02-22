ARG FROM_IMAGE=baserow/baserow:1.9
FROM $FROM_IMAGE as image_base
FROM cloudron/base:3.0.0@sha256:455c70428723e3a823198c57472785437eb6eab082e79b3ff04ea584faf46e92

ENV DOCKER_USER=cloudron
ENV DATA_DIR=/app/data
ENV POSTGRES_VERSION=14
ENV POSTGRES_LOCATION=/etc/postgresql/14/main/

# ========================
# = INSTALL DEPENDENCIES
# ========================
RUN apt-get update && apt-get upgrade -y && \
    DEBIAN_FRONTEND=noninteractive TZ=Etc/UTC apt-get install --no-install-recommends -y \
    make supervisor curl gnupg2 \
    build-essential \
    libpq-dev \
    redis-server \
    python3 \
    python3-pip \
    python3-dev \
    python3-venv \
    ca-certificates \
    tini \
    gosu

RUN curl -fsSL https://deb.nodesource.com/setup_12.x | bash -

RUN apt-get install --no-install-recommends -y nodejs && rm -rf /var/cache/apt /var/lib/apt/lists

# ========================
# = BASEROW_CADDY
# ========================
RUN curl -o caddy.tar.gz -sL https://github.com/caddyserver/caddy/releases/download/v2.4.6/caddy_2.4.6_linux_amd64.tar.gz && \
    tar -xf caddy.tar.gz && \
    mv caddy /usr/bin/ && \
    rm caddy.tar.gz

# ========================
# = SUPERVISOR
# ========================
# Ensure supervisor logs to stdout
RUN ln -sf /dev/stdout /var/log/supervisor/supervisord.log

# ========================
# = REDIS
# ========================
# Ensure redis is not running in daemon mode as supervisor will supervise it directly
# Point redis at our data dir
# Ensure redis logs to stdout by removing any logfile statements
# Sedding changes the owner, change it back.
RUN usermod -a -G tty redis && \
    sed -i 's/daemonize yes/daemonize no/g' /etc/redis/redis.conf && \
    sed -i 's/daemonize no/daemonize no\nbind 127.0.0.1/g' /etc/redis/redis.conf && \
    sed -i '/^logfile/d' /etc/redis/redis.conf && \
    chown redis:redis /etc/redis/redis.conf

# ========================
# = BASEROW
# ========================
COPY --chown=cloudron:cloudron --from=image_base /baserow/ /baserow/
# The copy above will have chowned the supervisor folder to cloudron user when it should
# be root.
RUN chown -R root:root /baserow/supervisor
# Virtualenvs are not portable and especially not so between image_base which is debian
# and focal (cloudron/base). We install our python venv here instead.
RUN rm /baserow/venv -rf && \
    python3 -m pip install --no-cache-dir --no-warn-script-location --disable-pip-version-check --upgrade pip==22.0.3 && \
    python3 -m pip install --no-cache-dir --no-warn-script-location --upgrade virtualenv==20.13.1 && \
    python3 -m virtualenv /baserow/venv
# hadolint ignore=SC1091
RUN . /baserow/venv/bin/activate && pip3 install --no-cache-dir -r /baserow/backend/requirements/base.txt

RUN cd /baserow/web-frontend && yarn install && yarn build && chown cloudron: -R /baserow/web-frontend/

COPY deploy/cloudron/cloudron_env.sh /baserow/supervisor/env/cloudron_env.sh
COPY deploy/all-in-one/baserow.sh /baserow.sh

ENTRYPOINT ["/baserow.sh"]
CMD ["start"]
