# Install on Ubuntu (WIP)

Install Baserow on a clean server running Ubuntu. (WIP)

While writing this tutorial I used a clean Droplet at Digital Ocean running Ubuntu 
18.04.3 LTS. We also expect root access.

# First things first

Because we have a clean server we need to update the packages first.

```
$ sudo apt-get update
$ sudo apt-get -y upgrade
```

## PostgreSQL

```
$ sudo apt-get install -y postgresql postgresql-contrib
$ sudo -u postgres psql
postgres=# create database baserow;
postgres=# create user baserow with encrypted password 'test12';
postgres=# grant all privileges on database baserow to baserow;
postgres=# \q
```

## Baserow

```
$ sudo useradd baserow
$ sudo passwd baserow
Enter new UNIX password: test12
Retype new UNIX password: test12
$ mkdir /baserow
$ cd /baserow
$ git clone git@gitlab.com:bramw/baserow.git .

$ apt-get install python3 python3-pip virtualenv libpq-dev libmysqlclient-dev
$ virtualenv -p python3 backend/env
$ pip install -e ./backend

$ curl -sL https://deb.nodesource.com/setup_10.x | sudo -E bash -
$ apt-get install nodejs
$ curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | sudo apt-key add -
$ echo "deb https://dl.yarnpkg.com/debian/ stable main" | sudo tee /etc/apt/sources.list.d/yarn.list
$ sudo apt update
$ sudo apt install yarn
$ cd web-frontend
$ yarn install
```

## NGINX

```
$ sudo apt-get install nginx
$ sudo /etc/init.d/nginx start
```

http://IP

```
$ 
```
