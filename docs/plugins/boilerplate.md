# Boilerplate

With the plugin boilerplate you can easily create a new plugin and setup a docker
development environment that installs Baserow as a dependency. It includes linters and
it can easily be installed via cookiecutter. It requires Baserow to live in the same
directory as the plugin so that it can install Baserow as a dependency.

## Creating plugin

Before the cookiecutter plugin boilerplate template can be used you first need to 
clone the Baserow repository and install cookiecutter. In this example I will 
assume you are working in an empty directory at `~/baserow` and that you have installed 
python and pip.

```
$ cd ~/baserow
$ pip install cookiecutter
$ git clone --branch master https://gitlab.com/bramw/baserow.git
Cloning into 'baserow'...
```

Inside the cloned repository lives the plugin boilerplate. By executing the following
command we are going to create a new plugin. For example purposes we will name this 
plugin "My Baserow Plugin". You can choose how you want to name your plugin via the 
cookiecutter input prompts.

> The python module depends on the given project name. If we for example go with 
> "My Baserow Plugin" the Django app name will be my_baserow_plugin and the Nuxt module
> name will be my-baserow-plugin.

```
$ cookiecutter baserow/plugin-boilerplate
project_name [My Baserow Plugin]: 
project_slug [my-baserow-plugin]: 
project_module [my_baserow_plugin]:
```

## Starting development environment

If you do not see any errors it means that your plugin has been created. Navigate to 
the created directory and start your development environment.

> It is required that the cloned baserow folder lives in the same directory as the 
> plugin directory.

```
$ cd my-baserow-plugin
$ docker network create baserow_plugin_default
$ docker-compose up -d
...
Starting my-baserow-plugin-mjml ... done
Starting my-baserow-plugin-db   ... done
Starting my-baserow-plugin-redis   ... done
Starting my-baserow-plugin-backend ... done
Starting my-baserow-plugin-web-frontend ... done
```

The development environment is now running, but the development servers have not yet 
been started. First we will apply all the migrations, sync the templates and start the
Django backend development server by executing the following commands.

```
$ docker exec -it my-baserow-plugin-backend bash
$ baserow migrate
$ baserow sync_templates
$ baserow runserver 0.0.0.0:8000
```

Once that is running you can verify if the server is running by visiting 
http://localhost:8001/api/groups/ in your browser. You should see a JSON response 
containing "Authentication credentials were not provided.". This means that everything
is working! Second we can install the node dependencies and start the Nuxt development
server. Open a new tab/window of your terminal and execute the following commands.

> You might need to restart the Celery worker when you have made changes.

Celery is used to broadcast real time changes asynchronous to other users. If you want
to use real time collaboration you also need to start the Celery worker. Open a new tab
or window in your terminal and execute the following commands.

```
$ docker exec -it my-baserow-plugin-backend bash
$ celery -A baserow worker -l INFO
```

> It could happen that you get a module not found error when are trying to start the
> Nuxt development server. This will most likely be because Baserow has been installed
> as a link dependency and this means that Baserow needs its own node_modules in order 
> to work. Execute the following command inside the web-frontend container to resolve
> the issue: `(cd /baserow/web-frontend && yarn install)`.

Finally you need to start the web-frontend server. Open a new tab or window in your
terminal and execute to following commands.

```
$ docker exec -it my-baserow-plugin-web-frontend bash
$ yarn install
$ yarn run dev
```

If both servers are running you can navigate to https://localhost:3001 in your browser
and you should see a Baserow login screen. This means that the development environment
is working!

## First changes

The most important part inside the my-baserow-plugin folder is the 
plugins/my_baserow_plugin folder. Here you will find all the code of your plugin. For
example purposes we are going to add a simple endpoint which always returns the same 
response, and we are going to show this text on a page in the web frontend.

### Backend changes

We want to expose an endpoint on the following url 
http://localhost:8001/api/my-baserow-plugin/example/ that returns a JSON response 
containing a title and some content. Modify/create the following files:

plugins/my_baserow_plugin/backend/src/my_baserow_plugin/api/views.py
```python
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny


class ExampleView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request):
        return Response({
            'title': 'Example title',
            'content': 'Example text'
        })
```

plugins/my_baserow_plugin/backend/src/my_baserow_plugin/api/urls.py
```python
from django.urls import re_path

from .views import ExampleView


app_name = 'my_baserow_plugin.api'
urlpatterns = [
    re_path(r'example/$', ExampleView.as_view(), name='example'),
]
```

With these change you should be able to visit the desired url in your browser and it 
should return the desired content.

### Web frontend changes

Now that we have our endpoint we want to show the response on a page in the 
web-frontend. Add/modify the following code.

> You might need to restart the Nuxt development server because the routes have changes
> and they are loaded by the module.js.

plugins/my_baserow_plugin/web-frontend/routes.js
```javascript
import path from 'path'

export const routes = [
  {
    name: 'example',
    path: '/example',
    component: path.resolve(__dirname, 'pages/example.vue'),
  },
]
```

plugins/my_baserow_plugin/web-frontend/pages/example.vue
```vue
<template>
  <div>
    {{ content }}
  </div>
</template>

<script>
export default {
  async asyncData({ app }) {
    const response = await app.$client.get('/my-baserow-plugin/example/')
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

If you now visit http://localhost:3001/example in your browser you should see a page
containing the title and content defined in the endpoint.

You should now have a basic idea on how to make some changes to Baserow via the plugin
boilerplate. The changes we have discussed here are of course for example purposes and
are only for giving you an idea about how it works.

## Linters

The linters on the web-frontend side should run automatically when the development 
server is running. You can also run the linters manually by running the following 
commands in the correct container.

* `make lint-python` (backend): all the python code will be checked with flake8.
* `make eslint` (web-frontend): all the javascript code will be checked with eslint.
* `make stylelint` (web-frontend): all the scss code will be checked with stylelint.

## Common problems

### Distribution not found

You could get an error like `pkg_resources.DistributionNotFound: The 
'baserow==*.*.*' distribution was not found and is required by the application` when 
starting the development for the first time in the backend container. This is because
the baserow directory is only being mounted after the image has been created and the
egg-info folder is missing then. You can fix this by running the command 
`make install-python-dependencies` in the backend container. That should generate the 
egg-info files in the correct folder.
