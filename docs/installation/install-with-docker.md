== Baserow

=== Run baserow with auto ssl

```bash
docker run \
  -d \
  --name baserow \
  -e BASEROW_PUBLIC_URLS=https://www.yourdomain.com \
  -v baserow_data:/baserow/data \
  -p 80:80 \
  -p 443:443 \
  baserow/baserow:1.8.2
```
=== Run baserow behind a reverse proxy already handling ssl

```bash
docker run \
  -d \
  --name baserow \
  -e BASEROW_PUBLIC_URLS=https://www.yourdomain.com \
  -e BASEROW_CADDY_GLOBAL_CONF="auto_https off" \
  -v baserow_data:/baserow/data \
  -p 80:80 \
  -p 443:443 \
  baserow/baserow:1.8.2
```

=== Run Baserow on a nonstandard HTTP port 

```bash
docker run \
  -d \
  --name baserow \
  -e BASEROW_PUBLIC_URLS=https://www.yourdomain.com:3001 \
  -v baserow_data:/baserow/data \
  -p 80:80 \
  -p 3001:3001 \
  baserow/baserow:1.8.2
```

=== Launch only the embedded Postgres server so the Baserow postgres database can be directly accessed

```bash 
docker run -it --rm -p 5432:5432 -v baserow_data:/baserow/data baserow/baserow:1.8.2 db_only 
# Now you can connect on your host machine to the Baserow postgres database at port 5432
```

=== Backup all of Baserow

This will backup:
1. Baserows postgres database (This will be a raw copy of the PGDATA dir and hence not
   easily portable, see the section below on how to backup just the postgres db in a
   more portable way.)
2. The Caddy config and data, this will include any runtime config changes you might
   have made to the caddy server and any SSL certificates/keys automatically setup by
   Caddy.
3. The Redis servers state. This is not strictly needed.

Baserow stores all of its state in the folder found in /baserow/data. We strongly
recommend you mount a docker volume into this location to persist Baserows data.
Otherwise if you remove the Baserow container you will loose all of your data.

The command below assumes you have been running Baserow with the
`-v baserow_data:/baserow/data` volume. Please change this argument accordingly if
you have mounted the /baserow/data folder differently.

```bash
# Ensure Baserow is stopped first before taking a backup.
docker stop baserow
docker run --rm -v baserow_data:/baserow/data -v $(pwd):/backup ubuntu tar cvf /backup/backup.tar /baserow/data
```

=== Restore all of Baserow
```bash
# Ensure Baserow is stopped first before taking a backup.
docker stop baserow
docker run --rm -v baserow_data:/baserow/data -v $(pwd):/backup ubuntu tar cvf /backup/backup.tar /baserow/data
docker run --rm -v new_baserow_data_volume $(pwd):/backup ubuntu bash -c "mkdir -p /baserow/data && cd /baserow/data && tar xvf /backup/backup.tar --strip 1"
```

=== Backup Baserows Postgres database

Baserow stores all of its own data in Postgres. To backup just this database you can
run the command below.

```bash 
# By default backs up to the backups folder in the baserow_data volume.
docker run -it --rm -v baserow_data:/baserow/data baserow backend_with_db backup -f /baserow/data/backups/backup.tar.gz
# Or backup to a file on your host instead run something like:
docker run -it --rm -v baserow_data:/baserow/data -v $(pwd):/baserow/host baserow backend_with_db backup -f /baserow/host/backup.tar.gz
```

=== Restore Baserow

When restoring Baserow you must ensure you are restoring into a brand new Baserow data
volume.
```bash
docker run -it --rm \
  -v old_baserow_data_volume_containing_the_backup_tar_gz:/baserow/old_data \
  -v new_baserow_data_volume_to_restore_into:/baserow/data \
  baserow backend_with_db restore -f /baserow/old_data/backup.tar.gz 
# Or to restore from a file on your host instead run something like:
docker run -it --rm \
  -v baserow_data:/baserow/data -v \
  $(pwd):/baserow/host \
  baserow backend_with_db restore -f /baserow/host/backup.tar.gz
```

== Running healthchecks on Baserow

The Dockerimage already defines a HEALTHCHECK command which will be used by software
that supports it. However if you wish to trigger a healthcheck yourself on a running
Baserow container then you can run:

```bash
docker exec baserow ./baserow.sh backend backend-healthcheck
```

== Running Baserows or Djangos management commands

You can run management commands on an existing Baserow container called baserow
by running the following to see the available commands:

```bash
docker exec baserow ./baserow.sh backend manage 
docker exec baserow ./baserow.sh backend manage 
```

== Customizing Baserow

=== Building your own image from Baserow

``````
FROM baserow/baserow:1.8.2

COPY custom_env.sh /baserow/supervisor/env/custom_env.sh

== Making Baserow available on a domain name

=== Without https 
By default if you set BASEROW_PUBLIC_URLS to a standard name like www.mydomain.com it will attempt
to automatically enable SSL. If you wish to disable this behaviour indicate this by
changing your BASEROW_PUBLIC_URLS to www.mydomain.com:80 and only bind on the HTTP port. 
