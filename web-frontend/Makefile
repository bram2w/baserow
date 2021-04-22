install-dependencies:
	yarn install

eslint:
	yarn run eslint || exit;

stylelint:
	yarn run stylelint || exit;

lint: eslint stylelint

lint-javascript: lint

jest:
	yarn run jest-all || exit;

test: jest

unit-test-watch:
	yarn run jest test/unit --watch || exit;
