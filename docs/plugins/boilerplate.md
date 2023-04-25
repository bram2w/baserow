# Boilerplate

With the plugin boilerplate you can easily create a new plugin and setup a docker
development environment that installs Baserow as a dependency. It includes linters and
it can easily be installed via cookiecutter.

> The structure used for Baserow plugins is not yet finalized and might change to
> support installation of plugins via a market-place available in Baserow.

## Creating a plugin

To use the plugin boilerplate you must first install
the [Cookiecutter](https://cookiecutter.readthedocs.io/en/stable/installation.html)
tool (`pip install cookiecutter`).

Once you have installed Cookiecutter you can execute the following command to create a
new Baserow plugin from our template. In this guide we will name our plugin "My Baserow
Plugin", however you can choose your own plugin name when prompted to by Cookiecutter.

> The python module depends on your chosen plugin name. If we for example go with
> "My Baserow Plugin" the Django app name should be my_baserow_plugin and the Nuxt module
> name will be my-baserow-plugin.

```bash
cookiecutter gl:baserow/baserow --directory plugin-boilerplate
project_name [My Baserow Plugin]: 
project_slug [my-baserow-plugin]: 
project_module [my_baserow_plugin]:
```

If you do not see any errors it means that your plugin has been created.

## Starting the development environment

Now to start your development environment please run the following commands:

```bash
cd my-baserow-plugin
# Enable Docker buildkit
export COMPOSE_DOCKER_CLI_BUILD=1
export DOCKER_BUILDKIT=1
# Set these variables so the images are built and run with the same uid/gid as your 
# user. This prevents permission issues when mounting your local source into
# the images.
export PLUGIN_BUILD_UID=$(id -u)
export PLUGIN_BUILD_GID=$(id -g)
# You can optionally `export COMPOSE_FILE=docker-compose.dev.yml` so you don't need to 
# use the `-f docker-compose.dev.yml` flag each time.
docker-compose -f docker-compose.dev.yml up -d --build
docker-compose -f docker-compose.dev.yml logs -f
```

The development environment is now running and can be accessed at **http://localhost**.

You can check the plugin is working by visiting the demo url **http://localhost/starting**.

## First changes

The most important part inside the `my-baserow-plugin` folder is the
`plugins/my_baserow_plugin` folder. Here you will find all the code of your plugin. For
example purposes we are going to add a simple endpoint which always returns the same
response, and we are going to show this text on a page in the web frontend.

### Backend changes

We want to expose an endpoint on the following url
**http://localhost/api/my-baserow-plugin/example/** that returns a JSON response
containing a title and some content. Create/Modify the following files:

First open `plugins/my_baserow_plugin/backend/src/my_baserow_plugin/api/views.py` and
add your new view below the existing `StartingView`.

```python
class ExampleView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request):
        return Response({
            'title': 'Example title',
            'content': 'Example text'
        })
```

Then modify `plugins/my_baserow_plugin/backend/src/my_baserow_plugin/api/urls.py` and
add your new view's url pattern.

```python
from django.urls import re_path

from .views import StartingView, ExampleView

app_name = 'my_baserow_plugin.api'
urlpatterns = [
    re_path(r"starting/$", StartingView.as_view(), name="starting"),
    re_path(r'example/$', ExampleView.as_view(), name='example'),
]
```

With these change you should be able to visit
the **http://localhost/api/my_baserow_plugin/example/**
endpoint which should return the desired content.

### Web frontend changes

Now that we have our endpoint we want to show the response on a page in the
web-frontend. Add/modify the following code.

Modify `plugins/my_baserow_plugin/web-frontend/modules/my-baserow-plugin/routes.js` and
add your new route after the existing 'starting' route:

```javascript
import path from 'path'

export const routes = [
    {
        name: 'starting',
        path: '/starting',
        component: path.resolve(__dirname, 'pages/starting.vue'),
    },
    {
        name: 'example',
        path: '/example',
        component: path.resolve(__dirname, 'pages/example.vue'),
    },
]
```

Add `plugins/my_baserow_plugin/web-frontend/modules/my-baserow-plugin/pages/example.vue`

```vue
<template>
  <div>
    {{ content }}
  </div>
</template>

<script>
export default {
  async asyncData({app}) {
    // TODO Make sure you change this url prefix to the underscore separated and 
    // lowercase name of your plugin.
    const response = await app.$client.get('my_baserow_plugin/example/')
    return response.data
  },
  head() {
    return {
      title: this.title,
    }
  },
}
</script>
```

Now you will need to restart the Nuxt development server because the routes have changes
and they are loaded by the module.js.
Run `docker-compose -f docker-compose.dev.yml restart` to do this.

If you now visit http://localhost/example in your browser you should see a page
containing the title and content defined in the endpoint.

You should now have a basic idea on how to make some changes to Baserow via the plugin
boilerplate. The changes we have discussed here are of course for example purposes and
are only for giving you an idea about how it works.

## Linters

After you have started the dev environment and the containers are all running you can
run the following commands to run the linters.

* `docker-compose -f docker-compose.dev.yml exec my-baserow-plugin /baserow.sh backend-cmd bash -c bash`
    * You are now in a shell inside your Baserow dev container.
    * `cd /baserow/data/plugins/my_baserow_plugin/web-frontend/`
    * Now you can run any commands you would like:
        * `yarn run eslint --fix`
        * `yarn run stylelint`
        * `yarn add your_dependency`
    * `cd /baserow/data/plugins/my_baserow_plugin/backend/`
    * Now you can run any commands you would like:
        * `black .`
        * `flake8`
* To run pytest database tests in your dev container you need to ensure your database
  user has the CREATEDB; permission. To do this you can run:
  * `docker-compose -f docker-compose.dev.yml exec -T my-baserow-plugin /baserow/supervisor/docker-postgres-setup.sh run <<< "ALTER USER baserow CREATEDB;"`
* Now to run pytest database tests you can:
  * `docker-compose -f docker-compose.dev.yml exec my-baserow-plugin /baserow.sh backend-cmd bash -c bash`
  * `cd /baserow/data/plugins/my_baserow_plugin/backend/`
  * `pytest`

## Next Steps

The [Creating a Plugin](./creation.md) guide contains further info on creating plugins.
Also see the README.md in the root of your plugin folder.
