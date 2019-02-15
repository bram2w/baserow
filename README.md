# Baserow

To first start Baserow make sure you have installed docker and docker-compose. After that execute the following commands.

```
docker network create baserow_default
docker-compose up -d
```

For now it's only possible to work on the frontend SCSS components. In order to do so you can execute the commands below and then visit http://localhost:8080 in your browser.

```
docker exec -it baserow bash
cd /baserow/web-frontend
yarn dev
```
