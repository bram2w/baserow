# Baserow introduction

## Architecture

Baserow consists of two main components:

1. The **backend** is a Python Django application that exposes a REST API. This is the
   core of Baserow and it does not have a user interface. The [API spec](./api.md) can 
   be found here. The persistent state is by default stored in a PostgreSQL database.
   MySQL and  SQLite are not supported at the moment, but will probably be in the
   future.
1. The **web frontend** is an application that serves as a user interface for the
   backend and is made in [NuxtJS](https://nuxtjs.org/) and 
   [Vue.js](https://vuejs.org/). It communicates to the backend via the REST API.

## Backend

The backend consists of the **core**, **api** and **database** apps. The package also
contains base settings that can be extended. The REST API is written as a decoupled 
component which is not necessary to run Baserow. It is highly recommended though. The
same goes for the database app, this is written als a plugin for Baserow. Without it
you would only have the core which only has functionality like authentication, groups 
and the application abstraction.

### Handlers

If you look at the code of the API views you will notice that they use classes like 
CoreHandler, TableHandler, FieldHandler etc. The API views are actually a REST API
shell around these handlers which are doing the actual job. The reason why we choose to
do it this way is that if we ever want to implement a Web Socket API, SOAP API or any 
other API we can also build that around the same handler. That way we never have to 
write code twice. It is also useful for when you want to do something via the command
line. If you for example want to create a new group you can do the following.

```python
from django.contrib.auth import get_user_model 
from baserow.core.handler import CoreHandler

User = get_user_model()
user = User.objects.get(pk=1)
group = CoreHandler().create_group(user, name='Example group')
```

## Web frontend

The web-frontend consists of the **core** and **database** modules. The package also 
contains some base config that can be extended. It is basically a user friendly shell 
around the backend that can run in your browser. It is made using 
[NuxtJS](https://nuxtjs.org/).

### Style guide

There is a style guide containing examples of all components on 
https://baserow.io/style-guide or if you want to see it on your local environment
http://localhost:8000/style-guide.

## Concepts

### Groups

A group can contain multiple applications. It can be used to define a company and in the
future it is going to be possible to invite extra users to a group. Every user in the 
group has access to all the applications within that group. Unfortunately it is not yet
possible to add extra users because the live collaboration feature has to be 
implemented first. Groups can easily be created, edited and deleted via the 
`baserow.core.handler.CoreHandler` and via the REST API.

### Applications

An application is more of an abstraction that can be added to a group. By default the 
database plugin is included which contains the database application. Via the 
"create new" button in the sidebar a new application instance can be created for the 
selected group. Once you click on it you will see a context menu with all the 
application types. Plugins can introduce new application types. Applications can easily
be created, edited and deleted via the `baserow.core.handler.CoreHandler` and via the 
REST API.

### Database plugin

More information about the concepts of the database application can be found on the
[database plugin introduction page](./database-plugin.md).

## Environment variables

In combination with the default settings and config the following environment variables
are accepted.

* `DATABASE_NAME` (default `baserow`): The database name of PostgreSQL database.
* `DATABASE_USER` (default `baserow`): The username for the PostgreSQL database.
* `DATABASE_PASSWORD` (default `baserow`): The password for the PostgreSQL database.
* `DATABASE_HOST` (default `db`): The hostname of the PostgreSQL server.
* `DATABASE_PORT` (default `5432`): The port of the PostgreSQL server.
* `MJML_SERVER_HOST` (default `mjml`): The hostname of the MJML TCP server. In the 
  development environment we use the `liminspace/mjml-tcpserver:latest` image.
* `MJML_SERVER_PORT` (default `28101`): The port of the MJML TCP server.
* `PUBLIC_BACKEND_DOMAIN` (default `localhost:8000`): The publicly accessible domain 
  name of the backend. For the development environment this is localhost:8000, but if 
  you for example change the port to 9000 this should be `localhost:9000`.
* `PUBLIC_BACKEND_URL` (default `http://localhost:8000`): The publicly accessible URL 
  of the backend. For the development environment this is `http://localhost:8000`, but 
  if you for example change the port to 9000 this should be `http://localhost:9000`. 
  You should be able to lookup this url with your browser.
* `PRIVATE_BACKEND_URL` (default `http://backend:8000`): Not only the browser, but also
  web-frontend server should be able to do HTTP requests to the backend. It might not 
  have access to the `PUBLIC_BACKEND_URL` or there could be a more direct route, 
  (e.g. from container to container instead of via the internet). In case of the 
  development environment the backend container be accessed via the `backend` hostname
  and because the server is also running on port 8000 inside the container, the private
  backend URL should be `http://backend:8000`.
* `PUBLIC_WEB_FRONTEND_DOMAIN` (default `localhost:3000`): The publicly accessible domain 
  name of the web-frontend. For the development environment this is localhost:3000, but
  if you for example change the port to 4000 this should be `localhost:4000`.
* `PUBLIC_WEB_FRONTEND_URL` (default `http://localhost:3000`): The publicly accessible 
  URL of the web-frontend. For the development environment this is 
  `http://localhost:3000`, but if you for example change the port to 4000 this should 
  be `http://localhost:4000`. You should be able to lookup this url with your browser.
* `FROM_EMAIL` (default `no-reply@localhost`): If the from email address of the emails
  that the platform sends. For example when the user requests a password change because
  he has forgotten it.
