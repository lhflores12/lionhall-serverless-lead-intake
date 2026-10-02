# lionhall-lead-intake

AWS Lambda + API Gateway lead-intake service for Lionhall Ventures. Accepts a
lead submission (name, phone, source, optional email/notes), validates it,
and writes it to DynamoDB.

## Structure

- `src/lambda_function.py` — the Lambda handler. Parses the request, runs
  validation, writes to DynamoDB, and returns a JSON response. Wraps the
  DynamoDB call in error handling so a failure returns a generic 500 instead
  of leaking the raw AWS exception to the caller.
- `src/validation.py` — pure-Python validation logic (required fields, phone
  format, email format). Deliberately has zero AWS dependencies so it can be
  unit tested in complete isolation.
- `tests/` — unit tests for both modules using Python's built-in `unittest`.
  The Lambda-handler tests stub `boto3`/`botocore.exceptions` via
  `sys.modules` so they run without real AWS credentials, network access, or
  the `moto` library.

## Running tests

```
python3 -m unittest discover tests
```

## Deployment

This is deployed as the `lionhall-lead-intake` Lambda function (Python 3.12)
behind an API Gateway endpoint, with a DynamoDB table for storage. The
`src/` files are uploaded directly as the function's source in the Lambda
console (no build step required — pure stdlib + boto3, which the Lambda
runtime provides).
