FROM baserow

# Install dev dependencies manually.
COPY --chown=$UID:$GID ./backend/requirements/dev.txt /tmp/dev-requirements.txt
RUN . /baserow/venv/bin/activate && pip3 install -r /tmp/dev-requirements.txt

ENV BASEROW_ALL_IN_ONE_DEV_MODE='true'
