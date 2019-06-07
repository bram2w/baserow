# Baserow

To first start Baserow make sure you have installed docker and docker-compose. After that execute the following commands.

```
$ docker network create baserow_default
$ docker-compose up -d
```

In order to start developing for the web frontend you need to execute the following commands.

```
# install web frontend dependencies
$ docker exec -it baserow bash
$ cd /baserow/web-frontend
$ yarn install
$ yarn run dev

# build for production and launch server
$ yarn run build
$ yarn start

# generate static project
$ yarn run generate

# lint
$ yarn run eslint
$ yarn run stylelint

# test
$ yarn run test
```

When the development server starts you can visit http://localhost:3000.
