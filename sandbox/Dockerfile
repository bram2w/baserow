FROM python:3.6

RUN apt-get update
RUN apt-get -y install make
RUN apt-get -y install curl
RUN apt-get -y install gnupg2

RUN curl -sL https://deb.nodesource.com/setup_10.x  | bash -
RUN apt-get -y install nodejs
RUN npm install -g yarn

ADD ./backend /backend
ADD ./web-frontend /web-frontend
ADD ./sandbox /sandbox

WORKDIR /backend
RUN make install-dependencies
RUN make install-dev-dependencies

ENV PYTHONPATH $PYTHONPATH:/backend/src:/sandbox/src
ENV DJANGO_SETTINGS_MODULE='sandbox.settings'

WORKDIR /sandbox
CMD tail -f /dev/null
