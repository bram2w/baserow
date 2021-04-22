FROM nginx:1.19.10

ARG UID
ENV UID=${UID:-9999}
ARG GID
ENV GID=${GID:-9999}

# The nginx image already creates a non-root user to run as, update its ids so they
# match the provided UID and GID we wish to build and run this image with.
# If GID or UID already exist that's OK no need to stop the build.
RUN groupmod -g ${GID} nginx
RUN usermod -u ${UID} -g ${GID} nginx

RUN rm /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/conf.d