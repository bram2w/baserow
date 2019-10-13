FROM node:10

ADD . /old-web-frontend

WORKDIR /old-web-frontend

RUN apt-get update && apt-get -y install make curl gnupg2
RUN yarn install

CMD tail -f /dev/null
