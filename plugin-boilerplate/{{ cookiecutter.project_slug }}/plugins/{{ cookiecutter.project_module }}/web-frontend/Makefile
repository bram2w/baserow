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