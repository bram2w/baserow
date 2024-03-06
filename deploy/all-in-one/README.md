## Baserow is an open source no-code database tool and Airtable alternative.

Create your own online database without technical experience. Our user-friendly no-code
tool gives you the powers of a developer without leaving your browser.

* A spreadsheet database hybrid combining ease of use and powerful data organization.
* Easily self-hosted with no storage restrictions or sign-up on https://baserow.io to
  get started immediately.
* Alternative to Airtable.
* Open-core with all non-premium and non-enterprise features under
  the [MIT License](https://choosealicense.com/licenses/mit/) allowing commercial and
  private use.
* Headless and API first.
* Uses popular frameworks and tools like [Django](https://www.djangoproject.com/),
  [Vue.js](https://vuejs.org/) and [PostgreSQL](https://www.postgresql.org/).

```bash
docker run -v baserow_data:/baserow/data -p 80:80 -p 443:443 baserow/baserow:1.23.0
```

## Quick Reference

* **Maintained By**: [baserow.io](https://baserow.io/contact)
* **Get Support At**: [The Baserow Community Forums](https://community.baserow.io)
* **Source Code Available At**: [gitlab.com/baserow/baserow](https://gitlab.com/baserow/baserow)
* **Docs At**: [baserow.io/docs](https://baserow.io/docs)
* **License**: Open-Core with all non-premium and non-enterprise code under the MIT
  license.

## Supported tags and Dockerfile Links

* [`X.Y.Z`](https://gitlab.com/baserow/baserow/-/blob/master/deploy/all-in-one/Dockerfile)
  Tagged by Baserow version.
* [`latest`](https://gitlab.com/baserow/baserow/-/blob/master/deploy/all-in-one/Dockerfile)
* [`develop-latest`](https://gitlab.com/baserow/baserow/-/blob/develop/deploy/all-in-one/Dockerfile) 
  This is a bleeding edge image from our development branch, use at your own risk.

## Quick Start

Run the command below to start a Baserow server running locally listening on port `80`.
You will only be able to connect to Baserow from the machine running the server via
`http://localhost`.

```bash
docker run \
  -d \
  --name baserow \
  -e BASEROW_PUBLIC_URL=http://localhost \
  -v baserow_data:/baserow/data \
  -p 80:80 \
  -p 443:443 \
  --restart unless-stopped \
  baserow/baserow:1.23.0
```

* Change `BASEROW_PUBLIC_URL` to `https://YOUR_DOMAIN` or `http://YOUR_IP` to enable
  external access.
* Add `-e BASEROW_CADDY_ADDRESSES=https://YOUR_DOMAIN` to enable
  [automatic Caddy HTTPS](https://caddyserver.com/docs/caddyfile/concepts#addresses).
* Optionally add `-e DATABASE_URL=postgresql://user:pwd@host:port/db` to use an external
  Postgresql.
* Optionally add `-e REDIS_URL=redis://user:pwd@host:port` to use an external Redis.

> There is a security flaw with docker and the ufw firewall.
> By default docker when exposing ports on 0.0.0.0 will bypass any ufw firewall rules
> and expose the above container publicly from your machine on its network. If this
> is not intended then run with the following ports instead:
> `-p 127.0.0.1:80:80 -p 127.0.0.1:443:443` which makes your Baserow only accessible
> from the machine it is running on.
> Please see https://github.com/chaifeng/ufw-docker for more information and how to
> setup ufw to work securely with docker.

## Image Feature Overview

The `baserow/baserow:1.23.0` image by default runs all of Baserow's various services in a
single container for ease of use. A quick summary of its features are:

* Runs a Postgres database and Redis server by default internally and stores all data in
  the `/baserow/data` folder inside the container.
* Set `DATABASE_URL` or the `DATABASE_...` variables to disable the internal postgres
  and instead connect to an external Postgres.
* Set `REDIS_URL` or the `REDIS_...` variables to disable the internal redis and instead
  connect to an external Postgres.
* Runs all services behind a pre-configured Caddy reverse proxy. Set
  `BASEROW_CADDY_ADDRESSES` to `https://YOUR_DOMAIN.com` and it will
  [automatically enable https](https://caddyserver.com/docs/automatic-https#overview) for
  you and store the keys and certs in `/baserow/data/caddy`.
* Provides a CLI for execing admin commands against a running Baserow container or
  running one off commands against just a Baserow data volume.

## Example Commands

See [Configuring Baserow](configuration.md) for more detailed information on all the
other environment variables you can configure.

### Using a Domain with automatic https

If you have a domain name and have correctly configured DNS then you can run the
following command to make Baserow available at the domain with
[automatic https](https://caddyserver.com/docs/automatic-https#overview) provided by
Caddy.

> Append `,http://localhost` to BASEROW_CADDY_ADDRESSES if you still want to be able to
> access your server from the machine it is running on using http://localhost. See
> [Caddy's Address Docs](https://caddyserver.com/docs/caddyfile/concepts#addresses)
> for all supported values for BASEROW_CADDY_ADDRESSES.

```bash
docker run \
  -d \
  --name baserow \
  -e BASEROW_PUBLIC_URL=https://www.REPLACE_WITH_YOUR_DOMAIN.com \
  -e BASEROW_CADDY_ADDRESSES=https://www.REPLACE_WITH_YOUR_DOMAIN.com \
  -v baserow_data:/baserow/data \
  -p 80:80 \
  -p 443:443 \
  --restart unless-stopped \
  baserow/baserow:1.23.0
```

### Behind a reverse proxy already handling ssl

```bash
docker run \
  -d \
  --name baserow \
  -e BASEROW_PUBLIC_URL=https://www.yourdomain.com \
  -v baserow_data:/baserow/data \
  -p 80:80 \
  --restart unless-stopped \
  baserow/baserow:1.23.0
```

### On a nonstandard HTTP port

```bash
docker run \
  -d \
  --name baserow \
  -e BASEROW_PUBLIC_URL=https://www.yourdomain.com:3001 \
  -v baserow_data:/baserow/data \
  -p 3001:80 \
  --restart unless-stopped \
  baserow/baserow:1.23.0
```

### With an external PostgresSQL server

```bash
docker run \
  -d \
  --name baserow \
  -e BASEROW_PUBLIC_URL=https://www.yourdomain.com \
  -e DATABASE_HOST=TODO \
  -e DATABASE_NAME=TODO \
  -e DATABASE_USER=TODO \
  -e DATABASE_PASSWORD=TODO \
  -e DATABASE_PORT=TODO \
  -v baserow_data:/baserow/data \
  -p 80:80 \
  -p 443:443 \
  --restart unless-stopped \
  baserow/baserow:1.23.0
```

### With an external Redis server

```bash
docker run \
  -d \
  --name baserow \
  -e BASEROW_PUBLIC_URL=https://www.yourdomain.com \
  -e REDIS_HOST=TODO \
  -e REDIS_USER=TODO \
  -e REDIS_PASSWORD=TODO \
  -e REDIS_PORT=TODO \
  -e REDIS_PROTOCOL=TODO \
  -v baserow_data:/baserow/data \
  -p 80:80 \
  -p 443:443 \
  --restart unless-stopped \
  baserow/baserow:1.23.0
```

### With an external email server

```bash
docker run \
  -d \
  --name baserow \
  -e BASEROW_PUBLIC_URL=https://www.yourdomain.com \
  -e EMAIL_SMTP=True \
  -e EMAIL_SMTP_HOST=TODO \
  -e EMAIL_SMTP_PORT=TODO \
  -e EMAIL_SMTP_USER=TODO \
  -e EMAIL_SMTP_PASSWORD=TODO \
  -e EMAIL_SMTP_USE_TLS= \
  -v baserow_data:/baserow/data \
  -p 80:80 \
  -p 443:443 \
  --restart unless-stopped \
  baserow/baserow:1.23.0
```

### Start just the embedded database

If you want to directly access the embedded Postgresql database then you can run:

```bash 
docker run -it \
  --rm \
  --name baserow \
  -p 5432:5432 \
  -v baserow_data:/baserow/data \
  baserow/baserow:1.23.0 \
  start-only-db 
# Now get the password from
docker exec -it baserow cat /baserow/data/.pgpass
# Finally connect on your host machine to the Baserow postgres database at port 5432
# the password above with the username `baserow`.
```

### Run a one off command on the database

If you want to run a one off backend command against your Baserow data volume without
starting Baserow normally you can do so with the `backend-cmd-with-db` argument like so:

```bash 
docker run -it \
  --rm \
  --name baserow \
  -v baserow_data:/baserow/data \
  baserow/baserow:1.23.0 \
  backend-cmd-with-db manage dbshell
```

## Application builder domains

The build in Caddy server is configured to automatically handle additional application
builder domains. Depending on the environment variables, it will also automatically
fetch SSL certificates for those domains.

By default, it will accept requests of any domain over the http protocol, which is
perfect if you have a proxy in front of Baserow. If `BASEROW_CADDY_ADDRESSES` starts
with `https` protocol, then it will redirect http requests to https, and will handle
the SSL certificate part automatically. This is recommended when the container is
directly exposed to the internet.

## Backing up and Restoring Baserow

Baserow stores all of its persistent data in the `/baserow/data` directory by default.
We strongly recommend you mount a docker volume into this location to persist
Baserows data so you do not lose it if you accidentally delete your Baserow container.

> The backup and restore operations discussed below are best done on a Baserow server
> which is not being used.

### Backup all of Baserow

This will backup:

1. Baserows postgres database (This will be a raw copy of the PGDATA dir and hence not
   easily portable, see the section below on how to backup just the postgres db in a
   more portable way.)
2. The Caddy config and data, this will include any runtime config changes you might
   have made to the caddy server and any SSL certificates/keys automatically setup by
   Caddy.
3. The Redis servers state. This is not strictly needed.

Otherwise if you remove the Baserow container you will lose all of your data.

The command below assumes you have been running Baserow with the
`-v baserow_data:/baserow/data` volume. Please change this argument accordingly if you
have mounted the /baserow/data folder differently.

```bash
# Ensure Baserow is stopped first before taking a backup.
docker stop baserow
docker run --rm -v baserow_data:/baserow/data -v $PWD:/backup ubuntu tar cvf /backup/backup.tar /baserow/data
```

### Restore all of Baserow

```bash
# Ensure Baserow is stopped first before taking a backup.
docker stop baserow
docker run --rm -v baserow_data:/baserow/data -v $PWD:/backup ubuntu tar cvf /backup/backup.tar /baserow/data
docker run --rm -v new_baserow_data_volume $PWD:/backup ubuntu bash -c "mkdir -p /baserow/data && cd /baserow/data && tar xvf /backup/backup.tar --strip 1"
```

### Backup only Baserow's Postgres database

Please ensure you only back-up a Baserow database which is not actively being used
by a running Baserow instance or any other process which is making changes to the
database.

Baserow stores all of its own data in Postgres. To backup just this database you can run
the command below.

```bash 
# First read the help message for this command
docker run -it --rm -v baserow_data:/baserow/data baserow/baserow:1.23.0 \
   backend-cmd-with-db backup
   
# By default backs up to the backups folder in the baserow_data volume.
docker run -it --rm -v baserow_data:/baserow/data baserow/baserow:1.23.0 \
   backend-cmd-with-db backup -f /baserow/data/backups/backup.tar.gz
   
# Or backup to a file on your host instead run something like:
docker run -it --rm -v baserow_data:/baserow/data -v $PWD:/baserow/host \
   baserow/baserow:1.23.0 backend-cmd-with-db backup -f /baserow/host/backup.tar.gz
```

### Restore only Baserow's Postgres Database

When restoring Baserow you must ensure you are restoring into a brand new Baserow data
volume.

```bash
docker run -it --rm \
  -v old_baserow_data_volume_containing_the_backup_tar_gz:/baserow/old_data \
  -v new_baserow_data_volume_to_restore_into:/baserow/data \
  baserow backend-cmd-with-db restore -f /baserow/old_data/backup.tar.gz 

# Or to restore from a file on your host instead run something like:
docker run -it --rm \
  -v baserow_data:/baserow/data -v \
  $(pwd):/baserow/host \
  baserow backend-cmd-with-db restore -f /baserow/host/backup.tar.gz
```

## Running healthchecks on Baserow

The Dockerfile already defines a HEALTHCHECK command which will be used by software
that supports it. However if you wish to trigger a healthcheck yourself on a running
Baserow container then you can run:

```bash
docker exec baserow ./baserow.sh backend-cmd backend-healthcheck
# Run the below to see all available healthchecks
docker exec baserow ./baserow.sh backend-cmd help 
```

## Running Baserow or Django management commands

You can run management commands on an existing Baserow container called baserow by
running the following to see the available commands:

```bash
docker exec baserow ./baserow.sh backend-cmd manage 
# For example you could migrate the database of a running Baserow using:
docker exec baserow ./baserow.sh backend-cmd manage migrate
```

## Customizing Baserow

### Mounting in a config file

Baserow will automatically source any `.sh` files found in `/baserow/supervisor/env/` or
`/baserow/data/env/` on startup. Use this to create a single config file to configure
your Baserow like so:

```bash
custom_baserow_conf.sh << EOF
export BASEROW_PUBLIC_URL=todo
export BASEROW_CADDY_ADDRESSES=todo

# You can perform any Bash logic required in here to setup Baserow conditionally.
EOF

docker run \
  -d \
  --name baserow \
  -e BASEROW_PUBLIC_URL=http://localhost \
  -v $PWD/custom_baserow_conf.sh /baserow/supervisor/custom_baserow_conf.sh \
  -v baserow_data:/baserow/data \
  -p 80:80 \
  -p 443:443 \
  --restart unless-stopped \
  baserow/baserow:1.23.0
```

Or you can just store it directly in the volume at `baserow_data/env` meaning it will
be loaded whenever you mount in this data volume.

### Building your own image from Baserow

```dockerfile
FROM baserow/baserow:1.23.0

# Any .sh files found in /baserow/supervisor/env/ will be sourced and loaded at startup
# useful for storing your own environment variable overrides.
COPY custom_env.sh /baserow/supervisor/env/custom_env.sh

# Set the DATA_DIR environment variable to change where Baserow stores its persistent 
# data. At startup Baserow will attempt to chown and setup this folder correctly.
ENV DATA_DIR=/baserow/data

# This image bakes in its own default user with UID/GID of 9999:9999 by default. To
# Set this to change the user Baserow will run its Caddy, backend, Celery and 
# web-frontend services as. However be warned, the default entrypoint needs to be run 
# as root so using USER may break things.
ENV DOCKER_USER=baserow_docker_user
```
