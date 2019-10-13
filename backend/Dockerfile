FROM python:3.6

ADD . /backend

WORKDIR /backend

ENV PYTHONPATH $PYTHONPATH:/backend/src

RUN apt-get update && apt-get -y install make curl gnupg2
RUN make install-dependencies

CMD tail -f /dev/null
