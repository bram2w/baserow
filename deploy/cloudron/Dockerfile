FROM cloudron/base:3.0.0@sha256:455c70428723e3a823198c57472785437eb6eab082e79b3ff04ea584faf46e92

RUN mkdir -p /app/code
WORKDIR /app/code

RUN curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | sudo apt-key add -

# We want to install Redis version 5.
RUN add-apt-repository ppa:chris-lea/redis-server
RUN apt-get update && \
    apt install -y \
    make curl gnupg2 nginx redis-server supervisor \
    python3 build-essential libxslt-dev python3-dev python3-virtualenv \
    python3-setuptools zlib1g-dev libffi-dev libssl-dev python3-pip \
    && rm -rf /var/cache/apt /var/lib/apt/lists

RUN service supervisor stop && service nginx stop
RUN rm -f /etc/nginx/sites-enabled/*

ADD start.sh /app/code
RUN git clone --branch master https://gitlab.com/bramw/baserow.git
RUN virtualenv -p python3 env
RUN env/bin/pip install --no-cache -r baserow/backend/requirements/base.txt
RUN (cd baserow/web-frontend && yarn install && yarn build)

RUN npm install -g mjml

RUN (mkdir -p /app/code/cloudron/cloudron && \
     mkdir /app/data && \
    touch /app/code/cloudron/cloudron/__init__.py)
ADD settings.py /app/code/cloudron/cloudron

ENV PYTHONPATH $PYTHONPATH:/app/code/baserow/backend/src:/app/code/cloudron
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8
ENV TMPDIR=/run/temp

USER root

RUN chown -R cloudron:cloudron /app/code

RUN sed -i 's/daemonize no/daemonize yes\nbind 127.0.0.1/g' /etc/redis/redis.conf
RUN sed -i 's/dir \/var\/lib\/redis/dir \/app\/data\/redis/g' /etc/redis/redis.conf
RUN ln -sf /dev/stdout /var/log/redis/redis-server.log

ADD supervisor.conf /etc/supervisor/conf.d/supervisor.conf
RUN ln -sf /dev/stdout /var/log/supervisor/supervisord.log
RUN ln -sf /dev/stdout /app/code/supervisord.log

ADD nginx.conf /etc/nginx/sites-enabled/nginx.conf
RUN ln -sf /dev/stdout /var/log/nginx/access.log
RUN ln -sf /dev/stderr /var/log/nginx/error.log

CMD ["/app/code/start.sh"]
