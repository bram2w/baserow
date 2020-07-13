install-python-dependencies:
	apt-get update && apt-get install -y libpq-dev postgresql postgresql-contrib
	pip install -r requirements.txt

install-python-dev-dependencies:
	pip install -r requirements.dev.txt

lint-python:
	flake8 plugins/{{ cookiecutter.project_module }}/backend || exit;

install-javascript-dependencies:
	yarn install

eslint:
	yarn run eslint || exit;

stylelint:
	yarn run stylelint || exit;

lint-javascript: eslint stylelint
