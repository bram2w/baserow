install-dependencies:
	yarn install

eslint:
	yarn run eslint || exit;

stylelint:
	yarn run stylelint || exit;

lint: eslint stylelint

lint-javascript: lint

jest:
	npx jest || exit;

test: jest

unit-test:
	npx jest --selectProjects unit --selectProjects premium || exit;

ci-test-javascript:
	npx jest --ci || exit;

unit-test-watch:
	npx jest test/unit --watch || exit;
