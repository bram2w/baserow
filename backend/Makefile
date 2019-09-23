install-dependencies:
	apt-get update && apt-get install -y libpq-dev postgresql postgresql-contrib
	pip install -r requirements/base.txt
	pip install -r requirements/dev.txt

lint:
	flake8 src/baserow || exit;

test:
	pytest tests || exit;
