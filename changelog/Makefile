install-dependencies:
	pip install -r requirements.txt

lint:
	flake8 src tests && \
	black . --extend-exclude='/generated/' --check && \
	isort --check --skip generated src tests && \
	bandit -r src/ \
	|| exit;

format:
	black . || exit;

sort:
	isort --skip generated  src tests || exit;

test:
	pytest tests || exit;
