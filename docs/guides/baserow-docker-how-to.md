# Baserow Docker how to

Find below a list of FAQs and common operations when working with Baserow's docker
environment.

> Docker version 19.03 is the minimum required to build Baserow. It is strongly
> advised however that you install the latest version of Docker available: 20.10.
> Please check that your docker is up to date by running `docker -v`.

See [baserow's docker api](../reference/baserow-docker-api.md) for the full details on
what commands and environment variables baserow's docker-compose and docker image's
support.

## How To

### View the logs

```bash
$ docker-compose logs 
```

### Run Baserow alongside existing services

Baserow's docker-compose files will automatically expose the `backend`, `web-frontend`
and `media` containers to your machine's network. If you already have applications or
services using those ports the Baserow service which uses that port will crash.

To fix this you can change which ports Baserow will use by setting the corresponding
environment variable:

- For `backend` set `BACKEND_PORT` which defaults to `8000`
- For `web-frontend` set `WEB_FRONTEND_PORT` which defaults to `3000`
- For `media` set `MEDIA_PORT` which defaults to `4000`

This is how to set these variables in bash:

```bash
$ BACKEND_PORT=8001 docker-compose up 
$ # or using dev.sh
$ BACKEND_PORT=8001 ./dev.sh
```

### Make Baserow publicly accessible

Please note, the Docker and compose files provided by Baserow are currently only
intended for local use. Exposing these containers publicly on the internet is not 
currently supported and is done at your own risk.

By default when you run `docker-compose up` you can only access Baserow from the same
machine by visiting `localhost:3000` or `127.0.0.1:3000`. If you are running the Baserow
docker containers on a remote server which you want to access over a network or the
public internet you need to set some environment variables to expose Baserow. 

> Please be warned that there is a security flaw with docker and the ufw firewall.
> By default docker when exposing ports on 0.0.0.0 will bypass any ufw firewall rules
> and expose the above containers publicly from your machine on the network. Please see
> https://github.com/chaifeng/ufw-docker for more information and how to setup ufw to
> work securely with docker.

You will need to set the following three environment variables to successfully expose
Baserow on your network.

1. `HOST_PUBLISH_IP=0.0.0.0` - This will configure `docker-compose.yml` to expose
   Baserow's containers on all IP addresses on the host machine, instead of just
   localhost. Warning: if you are using UFW please see the warning above.
2. `PUBLIC_BACKEND_URL={REPLACE_WITH_YOUR_DOMAIN_NAME_OR_HOST_IP}:8000` - This will
   ensure that Baserow clients will be able to successfully connect to the backend,
   if you can visit Baserow at port `3000` but you are getting API errors please ensure
   this variable is set correctly. If an IP address this must start with `http://` or 
   `https://`.
3. `PUBLIC_WEB_FRONTEND_URL={REPLACE_WITH_YOUR_DOMAIN_NAME_OR_HOST_IP}:3000` - The same
   variable as above but the URL for the web-frontend container instead.
   
Then you will need to go to `src/baserow/config/settings/base.py:16` and modify the
`ALLOWED_HOSTS` variable to include the hostname or IP address of the server that 
Baserow will be running on (the hostname/ip you will be typing into the
browser to access the site). For example adding a local network's IP would look like:
```python
ALLOWED_HOSTS = ["localhost", "192.168.0.194"]
```
   
One way of setting the 3 environment variables is below. Please replease `REPLACE_ME` 
with the IP address or domain name of the server where Baserow is running. Ensure that 
you prepend IP addresses with `http://` as shown in the second command below.

```bash
$ HOST_PUBLISH_IP=0.0.0.0 PUBLIC_BACKEND_URL=REPLACE_ME:8000 PUBLIC_WEB_FRONTEND_URL=REPLACE_ME:3000 docker-compose up --build
# For example running Baserow on a local network would look something like:
$ HOST_PUBLISH_IP=0.0.0.0 PUBLIC_BACKEND_URL=http://192.168.0.194:8000 PUBLIC_WEB_FRONTEND_URL=http://192.168.0.194:3000 docker-compose up --build
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

### Back-up your Baserow DB

Please read the output of `docker-compose run backend manage backup_baserow --help` and
the runbook found here [runbooks/back-up-and-restore-baserow.md](https://gitlab.com/bramw/baserow/-/blob/develop/docs/runbooks/back-up-and-restore-baserow.md.md)
before backing up your Baserow database. 

```bash
$ docker-compose build # Make sure you have built the latest images first
$ mkdir ~/baserow_backups
# The folder must be the same UID:GID as the user running inside the container, which
# for the local env is 9999:9999, for the dev env it is 1000:1000 or your own UID:GID
# when using ./dev.sh
$ sudo chown 9999:9999 ~/baserow_backups/ 
$ docker-compose run -e PGPASSWORD=baserow -v ~/baserow_backups:/baserow/backups backend manage backup_baserow -h db -d baserow -U baserow -f /baserow/backups/baserow_backup.tar.gz 
# backups/ now contains your Baserow backup.
```

### Restore your Baserow DB from a back-up

Please read the output of `docker-compose run backend manage restore_baserow --help` and
the runbook found here [runbooks/back-up-and-restore-baserow.md](https://gitlab.com/bramw/baserow/-/blob/develop/docs/runbooks/back-up-and-restore-baserow.md.md)
before restoring a Baserow database.

```bash
$ docker-compose build # Make sure you have built the latest images first
$ docker-compose run -e PGPASSWORD=baserow -v ~/baserow_backups/:/baserow/backups/ backend manage restore_baserow -h db -d baserow -U baserow -f /baserow/backups/baserow_backup.tar.gz
```

## Common Problems

### Build Error - Service 'backend' failed to build: unable to convert uid/gid chown

This error occurs when attempting to build Baserow's docker images with a version of
Docker earlier than 19.03. It can also occur when you are attempting to build Baserow
version 1.3 or earlier using a version of Docker less than 20.10. You can check your
local docker version by running `docker -v` and fix the error by installing the latest
version of Docker from https://docs.docker.com/get-docker/.

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
