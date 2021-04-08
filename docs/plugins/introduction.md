# Introduction

It is possible to add additional features to Baserow via plugins. Because the project
has been split into two components, the `backend` and `web-frontend`, you need a 
plugin for both. Since `backend` is built with Django, you can use the 
modular [apps](https://docs.djangoproject.com/en/2.2/ref/applications/) architecture.
Nuxt.js has a similar approach which can be used, but in Nuxt, plugins are called 
[modules](https://nuxtjs.org/guide/modules). If you want to see how a plugin 
works, you might want to a look at the database plugin in the main repository at 
`backend/src/baserow/contrib/database` and `web-frontend/modules/database`. The
database plugin is installed by default.

## Boilerplate

We highly recommend using the [plugin boilerplate](./boilerplate.md). You can easily 
start with everything you need using a cookiecutter template. All the python modules 
and javascript files are already in place and it comes with a docker development 
environment.
