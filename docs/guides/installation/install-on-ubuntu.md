# Installation on Ubuntu

This guide will walk you through a production installation of Baserow. Specifically this
document aims to provide a walkthrough for servers running Ubuntu 18.04.03 LTS. These instructions
have been tested with a clean install of Ubuntu 18.04.03 LTS and a user account with root access.
Note that without root access, many of the instructions cannot be executed, so root access is necessary
in almost all cases.

# Prerequisites
## Update & Upgrade Packages
In order to make sure that we're getting the correct and new versions of any packages we install, we need to update and upgrade our packages.

```bash
$ sudo apt update
$ sudo apt upgrade -y
```

## A quick note on firewalls
In order to serve web content you will need to open up the HTTP (and HTTPS) ports 80 (and 443). You can do this with a firewall - `ufw` might be good place to start if you are new to firewalls.

# Installation
## Install & Setup PostgreSQL
Baserow uses PostgreSQL in order to store its user data. You can install PostgreSQL with the following commands:

```
$ sudo apt install postgresql postgresql-contrib -y
$ sudo -u postgres psql
postgres=# create database baserow;
CREATE DATABASE
postgres=# create user baserow with encrypted password 'yourpassword';
CREATE ROLE
postgres=# grant all privileges on database baserow to baserow;
GRANT
postgres=# \q
```

Make sure that you use a secure password instead of `yourpassword`! Also take care that you use the password
you've chosen in any upcoming commands that need the PostgreSQL baserow user password.

## Install Baserow
In this section, we will install Baserow itself. We will need a new user called `baserow`. Baserow uses the `/baserow` directory
for storing the application itself. 

```bash
# Create baserow user
$ sudo useradd baserow
$ sudo passwd baserow
Enter new UNIX password: yourpassword
Retype new UNIX password: yourpassword

# Change to root user
$ sudo -i

# Clone the baserow project
$ mkdir /baserow
$ cd /baserow
$ git clone https://gitlab.com/bramw/baserow/ .
```

The password used for the `baserow` user does not have to be the same as the one used with PostgreSQL. Just make sure
that you use a secure password and that you remember it for when you need it later.

## Install dependencies for & setup Baserow
In order to use the Baserow application, we will need to create a virtual environment and install some more dependencies like: NodeJS, Yarn, Python 3.

```bash
# Install python3, pip & virtualenv
$ apt install python3 python3-pip virtualenv libpq-dev libmysqlclient-dev -y

# Create virtual environment
$ virtualenv -p python3 backend/env

# Activate the virtual environment
$ source backend/env/bin/activate

# Install backend dependencies through pip
$ pip3 install -e ./backend

# Deactivate the virtual environment
$ deactivate

# Install NodeJS
$ curl -sL https://deb.nodesource.com/setup_10.x | sudo -E bash -
$ apt install nodejs -y

# Install yarn
$ curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | sudo apt-key add -
$ echo "deb https://dl.yarnpkg.com/debian/ stable main" | sudo tee /etc/apt/sources.list.d/yarn.list
$ apt update
$ apt install yarn -y

# Install frontend dependencies through yarn
$ cd web-frontend
$ yarn install

# Build frontend
$ ./node_modules/nuxt/bin/nuxt.js build --config-file config/nuxt.config.demo.js
```


## Install NGINX
Baserow uses NGINX as a reverse proxy for it's frontend and backend. Through that, you can easily add SSL Certificates and 
add more applications to your server if you want to. 

```bash
# Go back to baserow root directory
$ cd /baserow

# Install & Start NGINX
$ apt install nginx -y
$ service nginx start
```

## Setup NGINX
If you're unfamiliar with NGINX: NGINX uses so called "virtualhosts" to direct web traffic from outside of your network to the correct application on your server. These virtual hosts are defined in `.conf` files which are put into the `/etc/nginx/sites-enabled/` directory where NGINX will then process them on startup. Baserow comes with two configuration files for NGINX. After moving these over, change the `server_name` value in both of the files. The server name is the domain under which you want Baserow to be reachable. 

Make sure that in the following commands you replace `api.domain.com` with your own backend domain and that you replace `baserow.domain.com` with your frontend domain.

```bash
# Move virtualhost files to /etc/nginx/sites-enabled/
$ cp docs/guides/installation/configuration-files/nginx/* /etc/nginx/sites-enabled/

$ rm /etc/nginx/sites-enabled/default

# Change the server_name values
$ sed -i 's/\*YOUR_DOMAIN\*/api.domain.com/g' /etc/nginx/sites-enabled/baserow-backend.conf
$ sed -i 's/\*YOUR_DOMAIN\*/baserow.domain.com/g' /etc/nginx/sites-enabled/baserow-frontend.conf

# Then restart nginx so that it processes the configuration files
$ service nginx restart
```

## Baserow Configuration
### Configuration
Baserow needs a few environment variables to be set in order to work properly. Here is a list of the environment variables with explanations for them. This list is solely for reference, there is no need to set these variables because they will be set through `supervisor` later on. This list does not describe all environment variables that can be set. For a better understanding of the available environment variables, take a look at `/baserow/backend/src/config/settings/base.py`.

We discourage changing the content of the `base.py` file since it might be overridden through a future update with `git pull`. It is only mentioned in this guide so that you're able to modify your Baserow instance as easily as possible with environment variables.

```
# Backend Domain & URL
PUBLIC_BACKEND_DOMAIN="api.domain.com"
PUBLIC_BACKEND_URL="https://api.domain.com"

# Frontend Domain & URL
PUBLIC_WEB_FRONTEND_DOMAIN="baserow.domain.com"
PUBLIC_WEB_FRONTEND_URL="https://baserow.domain.com"

# Private Backend URL & Database Password & Database Host
PRIVATE_BACKEND_URL="http://localhost"
DATABASE_PASSWORD="yourpassword"
DATABASE_HOST="localhost" 

# Django Settings Module & Python Path
DJANGO_SETTINGS_MODULE='baserow.config.settings.base'
PYTHONPATH=/baserow:/baserow/plugins/saas/backend/src

# Secret Key
SECRET_KEY="Something_Secret"
```

Baserow uses the secret key to generate a variety of tokens (e.g. password reset token, ...).
In order to generate a unique secret key, you can simply run the following command.

```bash
$ cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 80 | head -n 1
```

The output will be a alphanumeric string with 80 characters. You can shorten or lengthen the string by changing the number value in `fold -w 80` to a length you're satisfied with.

### Import relations into database
In the "*Install & Setup PostgreSQL*" Section, we created a database called `baserow` for the application. Since we didn't do anything with that database it is still empty, which will result in a non-working application since Baserow expects certain tables and relations to exist in that database. You can create these with the following commands:
```bash
# Prepare for creating the database schema
$ source backend/env/bin/activate
$ export DJANGO_SETTINGS_MODULE='baserow.config.settings.base'
$ export DATABASE_PASSWORD="yourpassword"
$ export DATABASE_HOST="localhost" 

# Create database schema
$ baserow migrate

$ deactivate
```

## Install & Configure Supervisor
Supervisor is an application that starts and keeps track of processes and will restart them if the process finishes. For Baserow this is used to reduce downtime and in order to restart the application in the unlikely event of an unforseen termination. You can install and configure it with these commands:

```bash
# Install supervisor
$ apt install supervisor -y

# Create folder for baserow logs
$ mkdir /var/log/baserow/

# Move configuration files
$ cd /baserow
$ cp docs/guides/installation/configuration-files/supervisor/* /etc/supervisor/conf.d/
```
You will need to edit the `baserow-frontend.conf` and `baserow-backend.conf` files (located now at `/etc/supervisor/conf.d/`) in order to set the necessary environment variables. You will need to change at least the following variables which can be found in the `environment=` section.

**Frontend**
- `PUBLIC_WEB_FRONTEND_URL`: The URL under which your frontend can be reached from the internet (HTTP or HTTPS)
-  `PUBLIC_BACKEND_URL`: The URL under which your backend can be reached from the internet (HTTP or HTTPS)
- `PUBLIC_WEB_FRONTEND_DOMAIN`: The domain under which you frontend can be reached from the internet (same as URL but without `https://`)
- `PUBLIC_BACKEND_DOMAIN`: The domain under which you backend can be reached from the internet (same as URL but without `https://`)

**Backend**
- `SECRET_KEY`: The secret key that is used to generate tokens and other random strings
- `DATABASE_PASSWORD`: The password of the `baserow` database user
- `DATABASE_HOST`: The host computer that runs the database (usually `localhost`)

After modifying these files you need to make supervisor reread the files and apply the changes.

```bash
# Stop NGINX service so that supervisor can take over
$ service nginx stop

# Read the newly added files
$ supervisorctl reread

# Apply the read changes
$ supervisorctl update

# Check if the startup worked correctly
$ supervisorctl status
```

If the `reread` oder the `update` command fail, try checking the logs at `/var/log/baserow/` - it is possible that another process is listening to one of the ports which would terminate NGINX, or parts of Baserow.

## HTTPS / SSL Support
Since you're probably serving private data with Baserow, we strongly encourage to use a SSL certificate to encrypt the traffic between the browser and your server. You can do that with the following commands. We will do that with certbot, which retrieves a SSL certificate from the LetsEncrypt Certificate Authority.

If you're not installing Baserow on a completely new server, you might need to remove previously installed `certbot` binaries from your machine. Consult the [certbot installation instructions](https://certbot.eff.org/lets-encrypt/ubuntubionic-nginx) for more information.

```bash
# Install certbot
$ sudo snap install core; sudo snap refresh core
$ sudo snap install --classic certbot

# Make certbot command available
$ sudo ln -s /snap/bin/certbot /usr/bin/certbot

# Start the certificate retrieval process
$ sudo certbot --nginx

# Restart nginx so that it reads the configuration created by certbot
$ supervisorctl restart nginx
```

## Ending
You now have a full installation of Baserow, which will keep the Front- & Backend running even if there is an unforeseen termination of them. 