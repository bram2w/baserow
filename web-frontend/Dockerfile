FROM node:10

ADD . /web-frontend

WORKDIR /web-frontend

RUN apt-get update && apt-get -y install make curl gnupg2
RUN make install-dependencies

CMD tail -f /dev/null
