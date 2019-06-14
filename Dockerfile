FROM python:3.6

ADD . /baserow

WORKDIR /baserow

ENV PYTHONPATH $PYTHONPATH:/baserow/backend/src

RUN apt-get update && apt-get -y install make curl gnupg2
RUN make install-dependencies

CMD tail -f /dev/null
