# {{ cookiecutter.project_name }}

## Baserow Plugins

A Baserow plugin can be used to extend or change the functionality of Baserow.
Specifically a plugin is a folder with a `backend` and/or `web-frontend` folder.

## How to run {{ cookiecutter.project_name }} using Docker-compose

A number of different example docker-compose files are provided in this folder. Before
using any of them it is recommended you set the following env variables:

```bash
# Enable Docker buildkit
export COMPOSE_DOCKER_CLI_BUILD=1
export DOCKER_BUILDKIT=1
# Set these variables so the images are built and run with the same uid/gid as your 
# actual user. This prevents permission issues when mounting your local source into
# the images.
export PLUGIN_BUILD_UID=$(id -u)
export PLUGIN_BUILD_GID=$(id -g)
```

1. `docker-compose.yml` - This is the simplest compose file that will run the your
   plugin installed into a single container, use `docker-compose up`.
2. `docker-compose.multi-service.yml` - This is a more complex compose file which runs
   each of the Baserow services with your plugin installed in separate containers all
   behind a Caddy reverse proxy.
    1. `docker-compose -f docker-compose.multi-service.yml up -d --build`
4. `docker-compose.dev.yml` - This is a development compose file which
   runs a Baserow all-in-one image with your plugin installed in development mode.
   Additionally, it will mount in the local source code into the container for hot code
   reloading.
   1. `docker-compose -f docker-compose.dev.yml up -d --build`
4. `docker-compose.multi-service.dev.yml` - This is a development compose file which
   runs the services in a separate containers like the `.multi-service.yml` above. The
   images used will be the development variants which have dev dependencies installed.
   Additionally, it will mount in the local source code into the containers so for hot
   code reloading.
   1. `docker-compose -f docker-compose.multi-service.dev.yml up -d --build`

## Missing features TODO

1. A templated setup guide in the generated folder itself.
2. Example tests for web-frontend and backend.
3. An equivalent dev.sh
4. Setup instructions for IDEs (vs-code/intellij)
5. Example GitLab/GitHub CI integration + instructions to publish plugin to Dockerhub.
