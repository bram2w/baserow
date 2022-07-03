# TODO before merge switch back to proper dockerhub image
FROM registry.gitlab.com/bramw/baserow/ci/baserow:ci-latest-432-update-plugin-boilterplate-and-docs-to-match-new-docker-usage

COPY ./plugins/{{ cookiecutter.project_module }}/ /baserow/plugins/{{ cookiecutter.project_module }}/
RUN /baserow/plugins/install_plugin.sh --folder /baserow/plugins/{{ cookiecutter.project_module }}
