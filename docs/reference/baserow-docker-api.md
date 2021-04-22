# Baserow's Docker API

Baserow uses docker and docker-compose when running the local or development
environments. Below you will find details on how this is structured, how to configure
baserow running this way and usage references.

## Baserow's Docker Files

Below are the files used by our docker setup and what they are responsible for:

### The Local Env

- `docker-compose.yml`: A compose file which starts Baserow in local mode with no
  development features enabled.
- `./backend/Dockerfile`: The backend's Dockerfile for local mode. See below for
  supported command line arguments. Also used to run the celery worker.
- `./web-frontend/Dockerfile`: The web-frontend's Dockerfile for local mode. See below
  for supported command line arguments.
- `./media/Dockerfile`: A simple nginx image used to serve uploaded user files only.

### The Dev Env

- `docker-compose.dev.yml`: A compose file which overrides parts of `docker-compose.yml`
  to enable development features, do not use this in production.
- `./backend/docker/Dockerfile.dev`: The backends's Dockerfile for dev mode.
- `./web-frontend/docker/Dockerfile.dev`: The web-frontend's Dockerfile for dev mode.

### For Both Envs

- `./backend/docker/docker-entrypoint.sh`: The entrypoint script used for both of the
  backend images.
- `./web-frontend/docker/docker-entrypoint.sh`: The entrypoint script used for both of
  the web-frontend images.

## Backend Image CLI

The `baserow_backend` and `baserow_backend_dev` images provide various commands used to
change what process is started inside the container.

```bash
Usage: docker run <imagename> COMMAND
Commands
local     : Start django using a prod ready gunicorn server
dev       : Start a normal Django development server
bash      : Start a bash shell
manage    : Start manage.py
python    : Run a python command
shell     : Start a Django Python shell
celery    : Run celery
celery-dev: Run a hot-reloading dev version of celery
lint:     : Run the linting
help      : Show this message
```

You can run one of these as a one off command like so:

```bash
# In the local environment
$ docker-compose run backend COMMAND
# In the dev environment
$ ./dev.sh run backend COMMAND
```

## Web Frontend CLI

The `baserow_web-frontend` and `baserow_web-frontend_dev` images provide various commands
used to change what process is started inside the container.

```bash
Usage: docker run <imagename> COMMAND
Commands
dev      : Start a normal nuxt development server
local    : Start a non-dev prod ready nuxt server
lint     : Run the linting
lint-fix : Run eslint fix
bash     : Start a bash shell
help     : Show this message
```

You can run one of these as a one off command like so:

```bash
# In the local environment
$ docker-compose run web-frontend COMMAND
# In the dev environment
$ ./dev.sh run web-frontend COMMAND
```

## Environment Variables

See [the introduction](../getting-started/introduction.md) for the environment variables
supported specifically by the backend and web-frontend processes. Below are the
variables available for configuring baserow's docker setup.

All of these variables can be set like so:

```bash
$ POSTGRES_PORT=5555 REDIS_PORT=6666 MJML_PORT=7777 docker-compose up 
$ # or using dev.sh
$ POSTGRES_PORT=5555 MIGRATE_ON_STARTUP=false ./dev.sh
```

### Local and Dev Variables

Port configuration (these only work when used with the docker-compose files):

- `POSTGRES_PORT` (default `5432`) : The port the `db` container will bind to on your
  local network.
- `REDIS_PORT` (default `6379`) : The port the `redis` container will bind to on your
  local network.
- `MJML_PORT` (default `28101`) : The port the `mjml` container will bind to on your
  local network.
- `BACKEND_PORT` (default `8000`) : The port the `backend` container will bind to on
  your local network.
- `WEB_FRONTEND_PORT` (default `3000`) : The port the `web-frontend` container will bind
  to on your local network.
- `MEDIA_PORT` (default `4000`) : The port the `media` nginx container will bind to on 
  your local network.

Backend configuration:

- `MIGRATE_ON_STARTUP` (default `true`) : When `true` on backend server startup it will
  perform a django migration before launching the backend server.
- `SYNC_TEMPLATES_ON_STARTUP` (default `true`) : When `true` on backend server startup
  it will run the baserow management command `sync_templates` which loads any templates
  found in `./backend/templates` into Baserow.

### Dev Only Variables 

- `UID` (default `1000` or your user id when using `./dev.sh`) : Sets which user id will
  be used to build Baserow's images with and the user id which will be used to run the
  processes inside Baserow containers.
- `GID` (default `1000` or your group id when using `./dev.sh`) : Sets which group id
  will be used to build Baserow's images with and the group id which will be used to run
  the processes inside Baserow containers.
