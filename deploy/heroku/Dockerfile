FROM ubuntu:focal

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update && \
    apt install -y \
    curl sudo gnupg2

RUN curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | sudo apt-key add - \
    && curl -sL https://deb.nodesource.com/setup_12.x  | bash -

RUN apt-get update && \
    apt install -y \
    make git nginx supervisor \
    python3 build-essential libxslt-dev python3-dev python3-virtualenv \
    python3-setuptools zlib1g-dev libffi-dev libssl-dev python3-pip \
    nodejs \
    && rm -rf /var/cache/apt /var/lib/apt/lists

RUN adduser --uid 1000 --disabled-login --gecos 'Heroku' heroku && \
    passwd -d heroku

RUN mkdir -p /baserow
WORKDIR /baserow

RUN service supervisor stop && service nginx stop
RUN rm -f /etc/nginx/sites-enabled/*

RUN git clone https://gitlab.com/bramw/baserow.git
# @TODO replace this with `master`
RUN git checkout 170-add-a-guide-to-deploy-on-heroku
RUN virtualenv -p python3 env
RUN env/bin/pip install --no-cache -r baserow/backend/requirements/base.txt
RUN (cd baserow/web-frontend && yarn install && yarn build)

RUN npm install -g mjml

RUN (mkdir -p /baserow/heroku/heroku && \
     mkdir /baserow/media && \
    touch /baserow/heroku/heroku/__init__.py)
ADD settings.py /app/code/heroku/heroku

ENV PYTHONPATH $PYTHONPATH:/baserow/baserow/backend/src:/baserow/heroku
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8
ENV TMPDIR=/run/temp

USER root

RUN chown -R heroku:heroku /baserow

ADD supervisor.conf /etc/supervisor/conf.d/supervisor.conf
RUN ln -sf /dev/stdout /var/log/supervisor/supervisord.log
RUN ln -sf /dev/stdout /app/code/supervisord.log

ADD nginx.conf /etc/nginx/sites-enabled/nginx.conf
RUN ln -sf /dev/stdout /var/log/nginx/access.log
RUN ln -sf /dev/stderr /var/log/nginx/error.log
