# Installation on Ubuntu

> Any questions, problems or suggestions with this guide? Ask a question in our
> [community](https://community.baserow.io/) or contribute the change yourself at
> https://gitlab.com/bramw/baserow/-/tree/develop/docs .

> If you installed Baserow 1.8.2 or earlier using this guide in version 1.8.2 please
> See the upgrade section at the end of this guide.

This guide will walk you through a production installation of Baserow using Docker 
on Ubuntu. This document aims to provide a walkthrough for servers running Ubuntu 
20.04.4 LTS. These instructions have been tested with a clean install of Ubuntu 
20.04.4 LTS and a user account with root access or the ability to run Docker containers. 

# Guide 

```bash
# Ensure your system is upto date
sudo apt update
# Docker Setup
sudo apt install docker
# Your user must be in the Docker group to run docker commands
sudo usermod -aG docker $USER
# Refresh the group so you don't need to relog to get docker permissions
newgrp docker 
# Change BASEROW_PUBLIC_URL to your domain name or http://YOUR_SERVERS_IP if you want
# to access Baserow remotely.
# This command will run Baserow with it's data stored in the new baserow_data docker 
# volume.
docker run -e BASEROW_PUBLIC_URL=http://localhost \
--name baserow \
-d \
--restart unless-stopped \
-v baserow_data:/baserow/data \
-p 80:80 \
-p 443:443 \
baserow/baserow:1.8.3
# Watch the logs for Baserow to come available by running:
docker logs baserow
```

# Further information 

Please refer to the [Install with Docker](install-with-docker.md) guide for how to
configure and maintain your Docker based Baserow server.

# Upgrade from Baserow 1.8.2 or earlier

The [Old Install on Ubuntu](old-install-on-ubuntu.md) guide is now deprecated. We are 
asking any users who wish to run Baserow on Ubuntu to instead install Docker and use our
official Docker images to run Baserow. This guide explains how to migrate an existing
Baserow Ubuntu install to use our official Docker images.

## Migration Steps

```bash
# Setup docker
sudo apt-get update
sudo apt-get install docker
sudo apt install docker
sudo usermod -aG docker $USER
# When you are ready to stop your old Baserow server by running
supervisorctl stop all
# Change BASEROW_PUBLIC_URL to your domain name or http://YOUR_SERVERS_IP if you want
# to access Baserow remotely.
# This command will run Baserow so it uses your existing postgresql database and your
# existing user uploaded files in /baserow/media. 
# It will store it's redis database and password, any data related to the automatic 
# HTTPS setup provided by Caddy in the new baserow_data docker volume.
docker run \
  -d \
  --name baserow \
  -e BASEROW_PUBLIC_URL=http://localhost \
  -e DATABASE_URL=postgresql://baserow:baserow@localhost:5432/baserow \
  --restart unless-stopped \
  -v baserow_data:/baserow/data \
  -v /baserow/media:/baserow/data/media \
  -p 80:80 \
  -p 443:443 \
  baserow/baserow:1.8.3
# Check the logs and wait for Baserow to become available
docker logs baserow
```

