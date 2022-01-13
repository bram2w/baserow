install-dependencies:
	apt-get update && apt-get install -y libpq-dev postgresql-client
	pip install -r requirements/base.txt

install-dev-dependencies:
	pip install -r requirements/dev.txt

lint:
	flake8 src tests ../premium/backend && black . ../premium/backend --extend-exclude='/(generated|migrations)/' --check || exit;

lint-python: lint

format:
	black . ../premium/backend --extend-exclude='/(generated|migrations)/' || exit;

test:
	pytest tests ../premium/backend/tests || exit;

test-parallel:
	pytest tests ../premium/backend/tests -n 10 || exit;
