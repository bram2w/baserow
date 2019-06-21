# Baserow

To first start Baserow make sure you have installed docker and docker-compose. After that execute the following commands.

```
$ docker network create baserow_default
$ docker-compose up -d
```

If you just want to try out the application I recommend using the sandbox environment to start. First you need to open bash in the just created container and then you should navigate to the sandbox directory, start the django development server, start the nuxt development server and visit http://localhost:3000 in your browser. An example of the commands is described below.

```
# terminal window 1
$ docker exec -it baserow bash
$ cd /baserow/sandbox
$ yarn install
$ yarn run dev

# terminal window 2
$ docker exec -it baserow bash
$ cd /baserow/sandbox
$ python manage.py runserver 0.0.0.0:8000
```

Both servers should be running and if you visit http://localhost:3000 you should see a working version of Baserow.

## Development

In order to start developing for the backend you need to execute the following commands.

```
docker exec -it baserow bash
cd /baserow/backend/src/baserow
python manage.py runserver 0.0.0.0:8000
```

In order to start developing for the web frontend you need to execute the following commands. Note that the backend server must also be running.

```
$ docker exec -it baserow bash
$ cd /baserow/web-frontend
$ yarn install
$ yarn run dev
```

When the development servers are on you can visit http://localhost:3000.

## Testing and linting

There are a few commands you can use inside the container to test and lint parts of the code.

```
$ docker exec -it baserow bash
$ cd /baserow

# run pytest for the backend
$ make lint-backend

# run flake8 for the backend
$ make test-backend

# run jest for the web frontend
$ make test-web-frontend

# run eslint for the web frontend
$ make eslint-web-frontend

# run stylelint for the web frontend
$ make stylelint-web-frontend
```
