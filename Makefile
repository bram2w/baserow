install-web-frontend-dependencies:
	curl -sL https://deb.nodesource.com/setup_10.x | bash
	apt-get install -y nodejs

	curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | apt-key add -
	echo "deb https://dl.yarnpkg.com/debian/ stable main" | tee /etc/apt/sources.list.d/yarn.list
	apt-get update && apt-get install -y yarn

	(cd web-frontend && yarn install)

install-backend-dependencies:
	apt-get update && apt-get install -y libpq-dev postgresql postgresql-contrib
	pip install -r backend/requirements/base.txt
	pip install -r backend/requirements/dev.txt

install-dependencies: install-backend-dependencies install-web-frontend-dependencies

eslint-web-frontend:
	(cd web-frontend && yarn run eslint) || exit;

stylelint-web-frontend:
	(cd web-frontend && yarn run stylelint) || exit;

lint-web-frontend: eslint-web-frontend stylelint-web-frontend

test-web-frontend:
	(cd web-frontend && yarn run test) || exit;

lint-backend:
	(cd backend && flake8 src/baserow) || exit;

test-backend:
	(cd backend && pytest tests) || exit;

lint: lint-backend lint-web-frontend
test: test-backend test-web-frontend
lint-and-test: lint test
