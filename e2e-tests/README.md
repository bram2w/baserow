## How to run locally

```bash
cd e2e-tests
# This will do all the yarn installs for you
./run-e2e-tests-locally.sh 
# Once done you can easily just re-run the following:
yarn run test
```

## How this runs in CI

All the CI does is essentially the following which you can run locally to reproduce
a CI run.

```bash
cd ..
./dev.sh build_only
cd e2e-tests
docker-compose up --build --exit-code-from e2e-tests
```

