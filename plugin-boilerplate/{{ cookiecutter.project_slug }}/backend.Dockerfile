# TODO before merge switch back to proper dockerhub image
FROM registry.gitlab.com/bramw/baserow/ci/backend:ci-latest-432-update-plugin-boilterplate-and-docs-to-match-new-docker-usage

USER root

COPY ./plugins/{{ cookiecutter.project_module }}/ $BASEROW_PLUGIN_DIR/{{ cookiecutter.project_module }}/
RUN /baserow/plugins/install_plugin.sh --folder $BASEROW_PLUGIN_DIR/{{ cookiecutter.project_module }}

USER $UID:$GID
