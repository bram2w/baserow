# Baserow

Open source data collaboration platform.

The complete toolchain for collaborating on any kind of data. One tool. Any device. Open
Source. Extendible. And we’re just getting started.

## Try out a demo

If you just want to try out Baserow you can easily start a demo environment via 
`docker-compose`. Just run the command following command and visit http://localhost:3000
in your browser

```
$ docker network create baserow_demo_default
$ docker-compose -f docker-compose.demo.yml up
```

## Plugin development

If you want to start developing a plugin I recommend using the sandbox environment. In 
there Baserow is installed as a dependency, exactly like and end user would have, if 
your plugin works in the sandbox it will work for everyone. Execute the following 
commands to get started. Note that the sandbox container might have a different name 
like `baserow_sandbox_1`.

```
$ docker network create baserow_default
$ docker-compose up -d
$ docker exec -it baserow_sandbox bash
$ python src/sandbox/manage.py migrate
$ python src/sandbox/manage.py runserver 0.0.0.0:8000
```

Open a new terminal window and execute the following commands.

```
$ docker exec -it baserow_sandbox bash
$ yarn install
$ yarn run dev
```

Now you'll have Baserow running, but installed as a dependency. To avoid conflicts the
backend now runs on port 8001 and the web-frontend on 3001, so if you visit 
http://localhost:3001 in your browser you should see a working environment. You can 
change the settings to add a Django app or Nuxt module. More documentation and a 
boilerplate for plugin development are going to follow soon.

## Core development

If you want to setup the development environment for core Baserow development you have 
to execute the following commands to start the backend part. Note that the sandbox 
container might have a different name like `backend_1`.

```
$ docker network create baserow_default
$ docker-compose up -d
$ docker exec -it backend bash
$ python src/baserow/manage.py migrate
$ python src/baserow/manage.py runserver 0.0.0.0:8000
```

In order to start the web-frontend environment you may execute the following commands. 
Note that the sandbox container might have a different name like `web-frontend_1`.

```
$ docker network create baserow_default
$ docker exec -it web-frontend bash
$ yarn install
$ yarn dev
```

Now you'll have the Baserow development environment running. Visit http://localhost:3000
in your browser and you should see a working version in development mode.
