# A small helper image which has some useful tools pre-installed that are used by ci
# stages. By building our own little image it means every single ci job doesn't need
# to repeatedly re-install these tools when they run.
FROM docker:20.10.18
ENV PYTHONUNBUFFERED=1
RUN apk add --update --no-cache curl git jq python3 openssh-client nodejs yarn docker-cli-compose bash && ln -sf python3 /usr/bin/python
RUN python3 -m ensurepip
RUN pip3 install --no-cache --upgrade pip setuptools
RUN mkdir /baserow && python3 -m venv /baserow/venv && . /baserow/venv/bin/activate && pip3 install coverage
