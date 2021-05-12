# Baserow Docker how to

Find below a list of FAQs and common operations when working with Baserow's docker
environment.

> Docker version 20.10.0 is the minimum required to build Baserow. Please check that
> your docker is up to date by running `docker -v`.

See [baserow's docker api](../reference/baserow-docker-api.md) for the full details on
what commands and environment variables baserow's docker-compose and docker image's
support.

## How To

### View the logs

```bash
$ docker-compose logs 
```

### Run Baserow alongside existing services

Baserow's docker-compose files will automatically bind to various ports on your
machine's network. If you already have applications or services using those ports the
Baserow service which uses that port will crash:

```bash
Creating network "baserow_local" with driver "bridge"
Creating db ... 
Creating db    ... error
Creating redis ... 
WARNING: Host is already in use by another container

Creating mjml  ... done
Creating redis ... done

ERROR: for db  Cannot start service db: driver failed programming external connectivity on endpoint db (...): Error starting userland proxy: listen tcp4 0.0.0.0:5432: bind: address already in use
ERROR: Encountered errors while bringing up the project.
```

To fix this you can change which ports Baserow will use by setting the corresponding
environment variable:

- For `postgres` set `POSTGRES_PORT` which defaults to `5432`
- For `redis` set `REDIS_PORT` which defaults to `6379`
- For `mjml` set `MJML_PORT` which defaults to `28101`
- For `backend` set `BACKEND_PORT` which defaults to `8000`
- For `web-frontend` set `WEB_FRONTEND_PORT` which defaults to `3000`
- For `media` set `MEDIA_PORT` which defaults to `4000`

This is how to set these variables in bash:

```bash
$ POSTGRES_PORT=5555 REDIS_PORT=6666 MJML_PORT=7777 docker-compose up 
$ # or using dev.sh
$ POSTGRES_PORT=5555 REDIS_PORT=6666 MJML_PORT=7777 ./dev.sh
```

### Configure an external email server

See [the introduction](../getting-started/introduction.md) for the all the of email
environment variables available to configure Baserow. For a simple example you can start
up Baserow locally and have it connect to an external SMTP server like so:

```bash
EMAIL_SMTP_HOST=TODO EMAIL_SMTP_PORT=TODO EMAIL_SMTP=True docker-compose up
```

### Change the container user

When running the dev env you can set the `UID` and `GID` environment variables when
building and running Baserow to change the user id and group id for the following
containers:

- backend
- celery
- web-frontend

> Remember you need to re-build if you change these variables or run `./dev.sh` from a
> new user.
> This is because Baserow's images build with file permissions set to the
> given `UID` and `GID`, so if they change without a re-build they will be incorrect.

When using `./dev.sh` it will automatically set `UID` and `GID` to the ids of the user
running the command for you.

### Disable automatic migration

You can disable automatic migration by setting the `MIGRATE_ON_STARTUP` environment
variable to `false` (or any value which is not `true`) like so:

```bash
$ MIGRATE_ON_STARTUP=false docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
$ # Or instead using ./dev.sh 
$ ./dev.sh dont_migrate  # dev.sh supports this as an explicit argument.
$ MIGRATE_ON_STARTUP=false ./dev.sh # or dev.sh will pass through whatever you have set. 
```

### Run a one off migration

```bash
# Run a one off dev container using the backend image which supports the "manage" command like so:
$ docker-compose -f docker-compose.yml -f docker-compose.dev.yml run backend manage migrate
$ # Or instead using ./dev.sh 
$ ./dev.sh run backend manage migrate
```

### Disable automatic template syncing

You can disable automatic baserow template syncing by setting the
`SYNC_TEMPLATES_ON_STARTUP` environment variable to `false` (or any value which is
not `true`) like so:

```bash
$ SYNC_TEMPLATES_ON_STARTUP=false docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
$ # Or instead using ./dev.sh 
$ ./dev.sh dont_sync # dev.sh supports this as an explicit argument.
$ SYNC_TEMPLATES_ON_STARTUP=false ./dev.sh # or dev.sh it will pass through whatever you have set. 
```

### Run a one off management command

```bash
# Run a one off dev container using the backend image which supports the "manage" command like so:
$ docker-compose -f docker-compose.yml -f docker-compose.dev.yml run backend manage sync_templates 
$ # Or instead using ./dev.sh 
$ ./dev.sh run backend manage sync_templates 
```

## Common Problems

### Build Error - Service 'backend' failed to build: unable to convert uid/gid chown

This error occurs when attempting to build Baserow's docker images with a version of
Docker earlier than 20.10.0. You can check your local docker version by
running `docker -v` and fix the error by installing the latest version of Docker from
https://docs.docker.com/get-docker/.

### Permission denied errors

If you used Baserow's dev env prior to April 2021 with the provided docker files you
might encounter permission errors in the containers when upgrading. With the old docker
files build output could end up being owned by root. These root owned files if they
still exist in your repo will cause a problem starting the new dev env as Baserow's
containers now run as a non-root user.

To fix simply ensure all files in your baserow git repo are owned by your current user
like so:

```bash
chown YOUR_USERNAME_HERE -R baserow/
```