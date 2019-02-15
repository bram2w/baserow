FROM ubuntu:18.04

ADD . /baserow

WORKDIR /baserow

RUN apt-get update && apt-get -y install make curl gnupg2
RUN make install-dependencies

CMD tail -f /dev/null
