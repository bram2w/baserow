install-dependencies:
	apt-get update && apt-get install -y libpq-dev postgresql-client
	pip install -r requirements/base.txt

install-dev-dependencies:
	pip install -r requirements/dev.txt

lint:
	flake8 src tests ../premium/backend && black . ../premium/backend --extend-exclude='/generated/' --check || exit;

lint-python: lint

format:
	black . ../premium/backend --extend-exclude='/generated/' || exit;

test:
	pytest tests ../premium/backend/tests || exit;

test-parallel:
	pytest tests ../premium/backend/tests -n 10 || exit;

ci-test-python:
	cd ..; \
	pytest \
	    backend/tests \
	    premium/backend/tests;

ci-check-startup-python:
	timeout --preserve-status 10s \
	    gunicorn --workers=1 -b 0.0.0.0:8002 \
	        -k uvicorn.workers.UvicornWorker baserow.config.asgi:application;
