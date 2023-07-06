install-dependencies:
	yarn install

eslint:
	yarn run eslint || exit;

stylelint:
	yarn run stylelint && yarn run prettier --check modules/**/*.scss || exit;

format-scss:
	yarn run prettier --write modules/**/*.scss || exit;

lint: eslint stylelint

lint-javascript: lint

jest:
	yarn test || exit;

test: jest

ci-test-javascript:
	yarn test-coverage || exit;
