install-dependencies:
	apt-get update && apt-get install -y libpq-dev postgresql postgresql-contrib
	pip install -r requirements/base.txt

install-dev-dependencies:
	pip install -r requirements/dev.txt

lint:
	flake8 src tests || exit;

format:
	black . || exit;

test:
	pytest tests || exit;
