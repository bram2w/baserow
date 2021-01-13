# Baserow

Open source online database tool and Airtable alternative.

**We're hiring** remote developers! More information at 
https://baserow.io/jobs/experienced-full-stack-developer.

![Baserow screenshot](docs/assets/screenshot.png "Baserow screenshot")

## Introduction

Create own database without technical experience. Our user friendly no-code tool gives
you the powers of a developer without leaving your browser.

* Uses popular frameworks like [Django](https://www.djangoproject.com/) and
  [Nuxt.js](https://nuxtjs.org/).
* Uses [PostgreSQL](https://www.postgresql.org/).
* Open source.
* MIT license.
* Self hosted.
* Headless and API first.
* Modular architecture.
* Supports plugins.
* Includes a plugin boilerplate.
* Unlimited rows.
* Runs in your browser.
* Alternative to Airtable.

## Become a sponsor

If you would like to get new features faster then you might want to consider becoming
a sponsor. By becoming a sponsor we can spend more time on Baserow which means faster
development.

[Become a GitHub Sponsor](https://github.com/sponsors/bram2w)

## Try out a demo

If you just want to try out Baserow, you can create an account on the SaaS version at
https://baserow.io. Just click on the create account or register button at the 
homepage.

If you want to try out Baserow on your own computer, you can easily start a demo 
environment via `docker-compose`. Just clone the repository, run the following commands
and visit http://localhost:3000 in your browser.

```
$ docker network create baserow_demo_default
$ docker-compose -f docker-compose.demo.yml up
```

More detailed instructions and more information about the demo environment can be found
[here](./docs/guides/demo-environment.md) or at 
https://baserow.io/docs/guides/demo-environment.

## Development environment

If you want to contribute to Baserow you need to setup the development environment. 
Execute the following commands to start the backend API server.

> Note that the container might have a different name like `backend_1`.

```
$ docker network create baserow_default
$ docker-compose up -d
$ docker exec -it backend bash
$ python src/baserow/manage.py migrate
$ python src/baserow/manage.py runserver 0.0.0.0:8000
```

Visit http://localhost:8000/api/groups/ in your browser and you should see a JSON 
response containing "Authentication credentials were not provided.". This means that it
is working!

In order to start the web-frontend environment you may execute the following commands.

```
$ docker network create baserow_default
$ docker exec -it web-frontend bash
$ yarn install
$ yarn dev
```

The Baserow development environment is now running. Visit http://localhost:3000 in your
browser and you should see a working version in development mode.

More detailed instructions and more information about the development environment can 
be found [here](./docs/development/development-environment.md) or at 
https://baserow.io/docs/development/development-environment.

## Plugin development

Because of the modular architecture of Baserow it is possible to create plugins. Make 
your own fields, views, applications, pages or endpoints. We also have a plugin 
boilerplate to get you started right away. More information can be found in the 
[plugin introduction](./docs/plugins/introduction.md) and in the 
[plugin boilerplate docs](./docs/plugins/boilerplate.md).

## Official documentation

The official documentation can be found on the website at https://baserow.io/docs/index
or [here](./docs/index.md) inside the repository. The API docs can be found here at 
https://api.baserow.io/api/redoc/ or if you are looking for the OpenAPI schema here
https://api.baserow.io/api/schema.json.

## Meta

Created by Bram Wiepjes (Baserow) - bram@baserow.io.

Distributes under the MIT license. See `LICENSE` for more information.

Version: 0.7.1

The official repository can be found at https://gitlab.com/bramw/baserow.

The changelog can be found [here](./changelog.md).

Become a GitHub Sponsor [here](https://github.com/sponsors/bram2w).

Community chat via https://gitter.im/bramw-baserow/community.
