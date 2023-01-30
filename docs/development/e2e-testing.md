# End-to-end testing

Baserow comes with end-to-end test suite in the `e2e-tests` folder. The test suite uses [Playwright](https://playwright.dev/) testing tool to run UI tests against a running Baserow instance using one or multiple browsers.

## Installation

Dependencies should be installed using the Yarn package manager:

```bash
$ cd e2e-tests
$ yarn install
```

Playwright browsers need to be installed as well:

```bash
# inside e2e-tests folder
$ yarn playwright install
```

## Running tests for development

You can use predefined `yarn` commands to run the test suite for local development without further configuration:

```bash
# inside e2e-tests folder
yarn test # headless
yarn test-headed
```

`yarn test` and `yarn test-headed` will run all tests in Chrome.

## Configuration

Besides Playwright configuration defined in `e2e-tests/playwright.config.ts` you can set environment variables to target a Baserow instance on any URL with `frontendBaseUrl` and `backendBaseUrl`. You can also use `e2e-tests/.env` file to do so, see `e2e-tests/.env-example`.
