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
