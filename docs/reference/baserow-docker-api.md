# Baserow's Docker API

Baserow uses docker and docker-compose when running the local or development
environments. Below you will find details on how this is structured, how to configure
baserow running this way and usage references.

## Baserow's Docker Files

Below are the files used by our docker setup and what they are responsible for:

### The Local Env

- `docker-compose.yml`: A compose file which starts Baserow in local mode with no
  development features enabled.
- `./backend/Dockerfile`: The backend's Dockerfile. See below for
  supported command line arguments. Also used to run the celery worker.
- `./web-frontend/Dockerfile`: The web-frontend's Dockerfile. See below
  for supported command line arguments.
- `./media/Dockerfile`: A simple nginx image used to serve uploaded user files only.

### The Dev Env

- `docker-compose.dev.yml`: A compose file which overrides parts of `docker-compose.yml`
  to enable development features, do not use this in production.
- `./backend/docker/Dockerfile`: Build with `--target dev` to get the dev version.
- `./web-frontend/docker/Dockerfile`: Build with `--target dev` to get the dev version. 

### For Both Envs

- `./backend/docker/docker-entrypoint.sh`: The entrypoint script used by the backend
  Dockerfile, provides a set of commonly used commands for working with baserow.
- `./web-frontend/docker/docker-entrypoint.sh`: The entrypoint script used by the 
   web-frontend Dockerfile, provides a set of commonly used commands for working
  with Baserow.

## Backend Image CLI

The `baserow_backend` and `baserow_backend_dev` images provide various commands used to
change what process is started inside the container.

```txt
Usage: docker run [-T] baserow_backend[_dev] COMMAND
Commands
local           : Start django using a prod ready gunicorn server
dev             : Start a normal Django development server
exec            : Exec a command directly.
bash            : Start a bash shell
manage          : Start manage.py
setup           : Runs all setup commands (migrate, update_formulas, sync_templates)
python          : Run a python command
shell           : Start a Django Python shell
celery          : Run celery
celery-dev:     : Run a hot-reloading dev version of celery
lint:           : Run the linting (only available if using dev target)
lint-exit       : Run the linting and exit (only available if using dev target)
test:           : Run the tests (only available if using dev target)
ci-test:        : Run the tests for ci including various reports (dev only)
ci-check-startup: Start up a single gunicorn and timeout after 10 seconds for ci (dev).
help            : Show this message
```

You can run one of these as a one off command like so:

```bash
# In the local environment
$ docker-compose run backend COMMAND
# In the dev environment
$ ./dev.sh run backend COMMAND
```

## Web Frontend CLI

The `baserow_web-frontend` and `baserow_web-frontend_dev` images provide various
commands used to change what process is started inside the container.

```txt
Usage: docker run [-T] baserow_web-frontend[_dev] COMMAND
Commands
dev      : Start a normal nuxt development server
local    : Start a non-dev prod ready nuxt server
lint     : Run all the linting
lint-fix : Run eslint fix
stylelint: Run stylelint
eslint   : Run eslint
test     : Run jest tests
ci-test  : Run ci tests with reporting
exec     : Exec a command directly.
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
$ BACKEND_PORT=8001 docker-compose up 
$ # or using dev.sh
$ BACKEND_PORT=8001 MIGRATE_ON_STARTUP=false ./dev.sh
```

### Local and Dev Variables

Port configuration (these only work when used with the docker-compose files):

- `HOST_PUBLISH_IP` (default `127.0.0.1`) : The IP address on the docker host Baserow's
  containers will bind exposed ports to. By default Baserow only exposes it's containers
  ports on localhost, please see
  the [Baserow Docker How To](../guides/baserow-docker-how-to.md)
  on how to expose Baserow over a network or the internet.
- `BACKEND_PORT` (default `8000`) : The port the `backend` container will bind to on
  your local network.
- `WEB_FRONTEND_PORT` (default `3000`) : The port the `web-frontend`
  container will bind to on your local network.
- `MEDIA_PORT` (default `4000`) : The port the `media` nginx container will bind to on
  your local network.

Backend configuration:

- `MIGRATE_ON_STARTUP` (default `true`) : When `true` on backend server startup it will
  perform a django migration before launching the backend server.
- `SYNC_TEMPLATES_ON_STARTUP` (default `true`) : When `true` on backend server startup
  it will run the baserow management command `sync_templates` which loads any templates
  found in `./backend/templates` into Baserow.

Pass through variables:

These environment variables when provided to the docker-compose files are passed through
to the correct containers. See [the introduction](../getting-started/introduction.md)
for what these variables do.

- `PUBLIC_BACKEND_URL`
- `PUBLIC_WEB_FRONTEND_URL`
- `MEDIA_URL`
- `EMAIL_SMTP`
- `EMAIL_SMTP_HOST`
- `EMAIL_SMTP_PORT`
- `EMAIL_SMTP_USE_TLS`
- `EMAIL_SMTP_USER`
- `EMAIL_SMTP_PASSWORD`
- `FROM_EMAIL`
- `DISABLE_ANONYMOUS_PUBLIC_VIEW_WS_CONNECTIONS`

### Dev Only Variables

- `UID` (default `1000` or your user id when using `./dev.sh`) : Sets which user id will
  be used to build Baserow's images with and the user id which will be used to run the
  processes inside Baserow containers.
- `GID` (default `1000` or your group id when using `./dev.sh`) : Sets which group id
  will be used to build Baserow's images with and the group id which will be used to run
  the processes inside Baserow containers.
- `POSTGRES_PORT` (default `5432`) : The port the `db` container will bind to on your
  local network.
