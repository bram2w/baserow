# Test Cases
This directory allows you to add test cases in JSON format that can be executed in both
the frontend and the backend.

## How to add a new case
Just add a file ending with `.json` in this directory and import it in your test file.

## How to implement a case
You can use `test.each` in the frontend and `@pytest.mark.parametrize` in the backend
to test each case defined in the JSON.
