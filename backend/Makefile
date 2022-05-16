install-dependencies:
	apt-get update && apt-get install -y libpq-dev postgresql-client
	pip install -r requirements/base.txt

install-dev-dependencies:
	pip install -r requirements/dev.txt

lint:
	flake8 src tests ../premium/backend && \
	black . ../premium/backend --extend-exclude='/generated/' --check && \
	bandit -r --exclude src/baserow/test_utils src/ ../premium/backend/src/ \
	|| exit;

lint-python: lint

format:
	black . ../premium/backend --extend-exclude='/generated/' || exit;

test:
	pytest tests ../premium/backend/tests || exit;

test-regenerate-ci-durations:
	pytest tests ../premium/backend/tests --store-durations || exit;

test-parallel:
	pytest tests ../premium/backend/tests -n 10 || exit;

PYTEST_SPLITS:=1
PYTEST_SPLIT_GROUP:=1
PYTEST_EXTRA_ARGS?=
ci-test-python:
	mkdir reports/ -p; \
	cd ..; \
	COVERAGE_FILE=backend/reports/.coverage.$(PYTEST_SPLIT_GROUP) \
	coverage run \
	    --rcfile=backend/.coveragerc \
	    -m pytest \
	    --durations-path=backend/.test_durations \
	    --splits $(PYTEST_SPLITS) \
	    --group $(PYTEST_SPLIT_GROUP) \
	    --junitxml=backend/reports/report.xml \
	    $(PYTEST_EXTRA_ARGS) \
	    backend/tests \
	    premium/backend/tests;

generate-html-coverage-report:
	mkdir html_coverage/ -p; \
	cd ..; \
	coverage run --rcfile=backend/.coveragerc -m pytest \
	    backend/tests \
	    premium/backend/tests; \
	coverage html -d html_coverage/;

ci-check-startup-python:
	timeout --preserve-status 10s \
	    gunicorn --workers=1 -b 0.0.0.0:8002 \
	        -k uvicorn.workers.UvicornWorker baserow.config.asgi:application;
