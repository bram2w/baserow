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
    libpq-dev \
    python3 build-essential libxslt-dev python3-dev python3-virtualenv \
    python3-setuptools zlib1g-dev libffi-dev libssl-dev python3-pip \
    nodejs \
    && rm -rf /var/cache/apt /var/lib/apt/lists

RUN npm install --global yarn mjml

RUN mkdir -p /baserow
WORKDIR /baserow

RUN service supervisor stop && service nginx stop
RUN rm -f /etc/nginx/sites-enabled/*

ADD . /baserow/baserow
RUN virtualenv -p python3 env
RUN env/bin/pip install --no-cache -r baserow/backend/requirements/base.txt
RUN env/bin/pip install dj-database-url boto3==1.16.25 django-storages==1.10.1
RUN (cd baserow/web-frontend && yarn install && yarn build)

RUN (mkdir -p /baserow/heroku/heroku && \
     mkdir /baserow/media && \
    touch /baserow/heroku/heroku/__init__.py)
ADD deploy/heroku/settings.py /baserow/heroku/heroku

ENV PYTHONPATH $PYTHONPATH:/baserow/baserow/backend/src:/baserow/baserow/premium/backend/src:/baserow/heroku
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8
ENV TMPDIR=/run/temp

ADD deploy/heroku/supervisor.conf /etc/supervisor/conf.d/supervisor.conf
RUN ln -sf /dev/stdout /var/log/supervisor/supervisord.log

ADD deploy/heroku/nginx.conf /baserow/nginx.conf
RUN ln -sf /dev/stdout /var/log/nginx/access.log
RUN ln -sf /dev/stderr /var/log/nginx/error.log

ADD deploy/heroku/entry.sh /baserow/entry.sh
RUN ["chmod", "+x", "/baserow/entry.sh"]
