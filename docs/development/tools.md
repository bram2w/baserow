# Development tools

## Backend

### PostgreSQL

By default Baserow uses PostgreSQL for persistent storage. In the near future MySQL and 
SQLite are also going to by supported, but this is not yet the case. Most things will
probably work with the other engines, but it will probably fail when converting a field
to another type. However, it hasn't yet been tested if the other engines work.

https://www.postgresql.org/

### Django

At the core of the backend we run the Django framework. A popular framework was chosen 
to lower the barrier of creating a plugin. We also looked for a batteries included, 
simple, and proven framework. Django was the obvious choice.

https://www.djangoproject.com

### Django REST framework

To quickly create endpoints, handle authentication, object serialization, validation, 
and do many more things we use Django REST Framework. You will find it at the base or
every endpoint.

https://www.django-rest-framework.org/

### pytest

We use pytest to easily and automatically test all the python code. Most of the backend
code is covered with tests and we like to keep it that way! The code is also tested
in the [continuous integration pipeline](./code-quality.md). It can also be tested 
manually in the development environment. Make sure that you are in the `backend` 
container and execute  the following command.

```
$ make test
```

https://docs.pytest.org/en/latest/contents.html

### Flake8

Flake8 makes it easy to enforce our python code style. The code is checked in the 
continuous integration pipeline. It can also be checked manually in the development
environment. Make sure that you are in the `backend` container and execute the 
following command. If all the code meets the standards you should not see any output.

```
$ make lint
```

https://flake8.pycqa.org/en/latest/

### Black 

Black auto formats all of our python code into one opinionated consistent style. The 
goal being to reduce and hopefully eliminate the need to worry about formatting whilst
writing and reviewing code.

https://black.readthedocs.io/en/stable/index.html

### ItsDangerous

In order to safely share sensitive data like password reset tokens we use a proven
library called ItsDangerous.

https://itsdangerous.palletsprojects.com/en/1.1.x/

### DRF spectacular

Having up to date API documentation and having it in the OpenAPI specification format 
is a must. To avoid mistakes, the contents are close to the code and are automated as 
much as possible. DRF Spectacular offers all of this!

https://pypi.org/project/drf-spectacular/

### MJML

In order to simplify the process of creating HTML emails we use MJML. This tool makes
it easy to create responsive emails that work with most email clients. This might seem
a bit like over engineering to use this for only the password forgot email, but more
complicated emails are going to be added in the future and we wanted to have a solid 
base. To make this integrate nicely with Django templates we use the liminispace
django mjml package.

https://mjml.io/
https://github.com/liminspace/django-mjml

## Web frontend

### Vue.js

https://vuejs.org/

### Nuxt.js

Because of our experience with Vue.js and the great features Nuxt.js offers, the choice
of Nuxt as a frontend framework was obvious. It offers server side rendering, automated 
code splitting, good project structure, modularity and lots of other features out of 
the box. All of which are needed for Baserow.

https://nuxtjs.org/

### Stylelint

The tool Stylelint is used to make sure all the SCSS code is in the correct format. It
is used when the `make stylelint` is called and live in the development environment via
prettier.

https://stylelint.io/

### ESLint

ESLint is used to make sure all the Javascript code is in the correct format. It is 
used when the `make eslint` is called and it runs live in the development environment
via prettier.

https://eslint.org/

### Prettier

https://prettier.io/

### webpack

Bundles all the assets of Baserow. This is being used by default with Nuxt.js.

https://webpack.js.org/

### SCSS

https://sass-lang.com/

### JEST

Because of its simplicity and compatibility with Vue and Nuxt we have chosen to include
JEST as the framework for the web frontend tests. Almost no code is covered yet so we
can definitely improve on that. The code is also tested in the continuous integration 
pipeline. It can also be tested manually in the development environment. Make sure 
that you are in the `web-frontend` container and execute the following command.

```
$ make jest
```

https://jestjs.io/

### Font Awesome 5

To improve the user experience we are using the Font Awesome icon set in the web 
frontend.

https://fontawesome.com/

## Thanks!

Big thanks to creators and contributors of the tools described above! Without you
Baserow would not have been where it is today.
