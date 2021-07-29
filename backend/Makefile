install-dependencies:
	apt-get update && apt-get install -y libpq-dev postgresql-client
	pip install -r requirements/base.txt

install-dev-dependencies:
	pip install -r requirements/dev.txt

lint:
	flake8 src tests plugins && black . --check || exit;

lint-python: lint

format:
	black . || exit;

test:
	pytest || exit;
