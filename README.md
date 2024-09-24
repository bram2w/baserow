## Baserow is an open source no-code database tool and Airtable alternative.

Create your own online database without technical experience. Our user-friendly no-code
tool gives you the powers of a developer without leaving your browser.

* A spreadsheet database hybrid combining ease of use and powerful data organization.
* Easily self-hosted with no storage restrictions or sign-up on https://baserow.io to
  get started immediately.
* Alternative to Airtable.
* Open-core with all non-premium and non-enterprise features under
  the [MIT License](https://choosealicense.com/licenses/mit/) allowing commercial and
  private use.
* Headless and API first.
* Uses popular frameworks and tools like [Django](https://www.djangoproject.com/),
  [Vue.js](https://vuejs.org/) and [PostgreSQL](https://www.postgresql.org/).

[![Deploy to Heroku](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/bram2w/baserow/tree/master)

```bash
docker run -v baserow_data:/baserow/data -p 80:80 -p 443:443 baserow/baserow:1.27.2
```
![Baserow screenshot](docs/assets/screenshot.png "Baserow screenshot")

## Features Overview
* No-Code Database Management: Create, manage, and share databases without writing any code.
* Collaborative: Work with your team in real-time with multi-user support.
* Self-Hosting: Full control over your data by hosting Baserow on your own server.
* Flexible API: Easily integrate Baserow with other applications using our API.
* Custom Fields and View: Customize your data tables with various field types (text, number, boolean, etc.) and views (grid, form, calendar).
* Modular Architecture: Extend functionality with plugins and custom features.

## Table of Contents
- [Introduction](#baserow-is-an-open-source-no-code-database-tool-and-airtable-alternative)
- [Features Overview](#features-overview)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Development Environment](#development-environment)
- [Plugin Development](#plugin-development)
- [Troubleshooting](#troubleshooting)
- [Versioning and Upgrades](#versioning-and-upgrades)
- [Official Documentation](#official-documentation)
- [Meta](#meta)




## Get Involved

**We're hiring remotely**! More information at https://baserow.io/jobs.

Join our forum on https://community.baserow.io/. See
[CONTRIBUTING.md](./CONTRIBUTING.md) on how to become a contributor.

## Installation

* [**Docker**](docs/installation/install-with-docker.md)
* [**Ubuntu**](docs/installation/install-on-ubuntu.md)
* [**Docker Compose** ](docs/installation/install-with-docker-compose.md)
* [**Heroku**: Easily install and scale up Baserow on Heroku.](docs/installation/install-on-heroku.md)
* [**Render**: Easily install and scale up Baserow on Render.](docs/installation/install-on-render.md)
* [**Digital Ocean**: Easily install and scale up Baserow on Digital Ocean.](docs/installation/install-on-digital-ocean.md)
* [**Cloudron**: Install and update Baserow on your own Cloudron server.](docs/installation/install-on-cloudron.md)
* [**Railway**: Install Baserow via Railway.](docs/installation/install-on-railway.md)
* [**Elestio**: Fully managed by Elestio.](https://elest.io/open-source/baserow)


## Quick Start
If you're new to Baserow, follow these quick steps to get started in minutes:
1. Install Docker on your machine from [here](https://www.docker.com/get-started).
2. Pull and run the Baserow Docker image:
   ```bash
   docker pull baserow/baserow:latest
3. Run the following command to start Baserow:
   docker run -v baserow_data:/baserow/data -p 80:80 -p 443:443 baserow/baserow:latest
4. Open http://localhost in your browser to access Baserow.


## Official documentation

The official documentation can be found on the website at https://baserow.io/docs/index
or [here](./docs/index.md) inside the repository. The API docs can be found here at
https://api.baserow.io/api/redoc/ or if you are looking for the OpenAPI schema here
https://api.baserow.io/api/schema.json.

## Become a sponsor

If you would like to get new features faster, then you might want to consider becoming a
sponsor. By becoming a sponsor we can spend more time on Baserow which means faster
development.

[Become a GitHub Sponsor](https://github.com/sponsors/bram2w)

## Development environment

If you want to contribute to Baserow you can setup a development environment like so:

```
$ git clone https://gitlab.com/baserow/baserow.git
$ cd baserow
$ ./dev.sh --build
```

The Baserow development environment is now running.
Visit [http://localhost:3000](http://localhost:3000) in your browser to see a working
version in development mode with hot code reloading and other dev features enabled.

More detailed instructions and more information about the development environment can be
found
at [https://baserow.io/docs/development/development-environment](./docs/development/development-environment.md)
.

## Plugin development

Because of the modular architecture of Baserow it is possible to create plugins. Make
your own fields, views, applications, pages or endpoints. We also have a plugin
boilerplate to get you started right away. More information can be found in the
[plugin introduction](./docs/plugins/introduction.md) and in the
[plugin boilerplate docs](./docs/plugins/boilerplate.md).

## Troubleshooting
## Issue: Docker container fails to start
* Solution: Make sure Docker is installed and running properly. You can check Docker’s status with the following command:
  ```bash
  docker ps
## If Docker isn't running, restart the service and try running the Baserow container again.


## Versioning and Upgrades
* To check the current version of Baserow running on your machine, use the following command:
```bash
docker exec -it baserow baserow version

## Support and Contact Information
If you encounter any issues while using Baserow, feel free to reach out to the support team or use the following resources:

* Community Forum: Join the discussion at [Baserow Community](https://community.baserow.io/).
* Documentation: Check our full [documentation](https://baserow.io/docs) for detailed guides and troubleshooting tips.
* Email Support: You can contact our support team directly at support@baserow.io.
* GitHub Issues: Report bugs or request features by creating an issue on our [GitHub repository](https://github.com/bram2w/baserow/issues).


## Meta

Created by Baserow B.V. - bram@baserow.io.

Distributes under the MIT license. See `LICENSE` for more information.

Version: 1.27.2

The official repository can be found at https://gitlab.com/baserow/baserow.

The changelog can be found [here](./changelog.md).

Become a GitHub Sponsor [here](https://github.com/sponsors/bram2w).
