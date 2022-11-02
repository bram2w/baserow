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
	npx jest --selectProjects unit --selectProjects premium --selectProjects enterprise || exit;

ci-test-javascript:
	JEST_JUNIT_OUTPUT_DIR=../reports/ npx jest -i --verbose --ci --forceExit --collectCoverage --coverageDirectory="./reports/coverage/" || exit;

unit-test-watch:
	npx jest test/unit --watch || exit;
