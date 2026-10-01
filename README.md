# Lionhall Serverless Lead Intake API

A real, deployed AWS serverless API that accepts a lead submission over HTTPS and writes it to a database, built as a hands-on portfolio piece demonstrating API Gateway, Lambda, DynamoDB, and IAM working together in production, not just as local code.

## What this is

A single HTTP endpoint, `POST /leads`, that a website form or any client can call with a lead's name, phone, and source. The request flows through API Gateway into a Lambda function, which validates the input and writes a structured record to DynamoDB. The function returns a generated lead ID and a 200 response on success, or a 400 with a clear error message on bad input.

It is a small system, intentionally. The point was not to build something complex, it was to build something real: deployed infrastructure a business could actually point a lead form at today, not a diagram or a local script.

## Why it matters

Most "I know AWS" claims on a resume are backed by tutorials or certifications with no running infrastructure behind them. This project is the opposite: an account-specific, deployed, tested, and verified system. Anyone can check that it works by sending it a request. That is the difference this project is meant to demonstrate for job applications in AWS/cloud and automation roles.

## Architecture

```
Client (curl / web form)
        |
        |  HTTPS POST /leads
        v
API Gateway (HTTP API)
   lionhall-lead-intake-api
        |
        |  Lambda proxy integration
        v
AWS Lambda (Python 3.12)
   lionhall-lead-intake
        |
        |  dynamodb:PutItem (scoped IAM role)
        v
DynamoDB table: LeadIntake
   partition key: leadId
```

Every arrow above is a real, deployed connection in the `438456517866` ("Lionhall AWS") account, `us-east-1`, verified end to end with a live `curl` request.

## Infrastructure and security decisions

| Decision | Why |
|---|---|
| DynamoDB on-demand capacity mode | No capacity planning needed for a low-volume lead intake table, pay only for what's used |
| Partition-key-only schema (`leadId`, a generated UUID) | Simplest correct design for a write-heavy, read-rarely intake table; no query patterns require a sort key |
| Lambda execution role scoped to exactly `dynamodb:PutItem` on the `LeadIntake` table ARN | Least privilege: the function only ever calls `put_item`, so the IAM policy grants nothing more, not even `GetItem` or access to any other table |
| Inline policy, not a managed "AdministratorAccess"-style grant | Keeps the permission auditable in one place, tied to this one role |
| HTTP API (not REST API) in API Gateway | Lower cost, lower latency, and simpler to configure for a single proxy-integration route; this project doesn't need REST API features like request validators or usage plans |
| Lambda proxy integration (payload format 2.0) | Lets the function own request/response shaping directly in code rather than configuring API Gateway mapping templates |
| Environment variable (`TABLE_NAME`) instead of hardcoding the table name | Standard 12-factor practice, makes the function portable across a dev/stage/prod table without a code change |
| CloudWatch Logs retention left at default (never expire) | Appropriate for a low-volume portfolio project; would be set to a fixed retention window in a cost-sensitive production system |

## Cost

This sits almost entirely inside AWS's always-free tiers:

- **Lambda**: 1M free requests/month and 400,000 GB-seconds of compute, permanently free tier
- **DynamoDB on-demand**: no minimum, billed per request; at portfolio-test volume this is fractions of a cent
- **API Gateway HTTP API**: 1M free requests/month for the first 12 months on a new account, then $1.00 per million requests after
- **CloudWatch Logs**: a few KB of logs per invocation, well under the 5GB free ingestion tier

Realistic cost running this as-is: effectively $0/month at low volume.

## How it was built

1. **DynamoDB table first** (`LeadIntake`), so the Lambda function had something real to write to while being developed.
2. **Lambda function and automated tests written and run locally before any AWS deploy.** Used `moto` (`@mock_aws`) to mock DynamoDB entirely in the test suite, so `pytest` runs in under 2 seconds with zero AWS calls and zero cost. Three tests: a valid lead creates an item, missing required fields returns 400, invalid JSON returns 400.
3. **GitHub repo + GitHub Actions CI** wired up before deploying, so every future push to `main` automatically installs dependencies and runs the full test suite. This mirrors how a real engineering team would gate changes, not just a personal script.
4. **IAM role scoped last-in-sequence, deliberately.** Lambda's console auto-creates a role with only CloudWatch Logs permissions; DynamoDB access was added as a second, explicit, scoped step, rather than requesting broad permissions up front "to make it work."
5. **API Gateway wired on top of the already-tested Lambda,** using a Lambda proxy integration so the function's own `_response()` helper controls the HTTP status and body, not API Gateway configuration.
6. **Verified with a real `curl` request** against the live endpoint, confirming a 200 response, a generated `leadId`, and (via the Lambda's CloudWatch log group being created on first invocation) that the full chain actually executed in AWS, not just in theory.

## Real problems hit and fixed

- **IAM inline-policy JSON editor auto-closes brackets.** Typing a full JSON policy character-by-character produced duplicate closing braces/brackets because the AWS console's code editor auto-inserts matching closers. Fixed by typing the policy without manually closing the outer object, letting the editor's auto-close handle the inner structure, then adding exactly the one missing outer `}`. Caught immediately because the console's inline JSON validator flags syntax errors before you can proceed.
- **Lambda console "Update" button is not "Deploy."** The top-right "Update" button on the Code source panel is actually a dropdown for uploading a `.zip` or an S3 object, not a way to deploy in-editor changes. The real deploy action is the "Deploy" button inside the editor's own sidebar. Caught via screenshot before it could cause a silent "my code didn't actually change" bug.
- **Dropped characters when typing into web forms via simulated keystrokes.** Both the GitHub repo description field and, in an earlier related session, LinkedIn profile fields occasionally lost characters when text was typed via simulated keyboard input. Standardized on setting form field values directly (bypassing simulated typing) for any single-field entry where precision matters.
- **Large code block needed to move from a tested local file into a browser-based editor without risk of silent corruption.** Typing a 35-line Python file character-by-character risks an undetectable partial typo in otherwise-correct, already-tested code. Used the Mac clipboard (`pbcopy` locally, paste in-browser) to move the exact file contents across, instead of either retyping or attempting a file upload (not possible here since the code lived outside any environment the browser automation could read from directly).

## AWS services and concepts demonstrated

| Service / concept | How it's used here |
|---|---|
| AWS Lambda | Python 3.12 function, environment variables, execution role |
| Amazon API Gateway (HTTP API) | Route configuration, Lambda proxy integration, auto-deploying stage |
| Amazon DynamoDB | On-demand table, partition key design, `put_item` writes |
| IAM | Least-privilege inline policy scoped to one action on one resource ARN |
| CloudWatch Logs | Automatic Lambda execution logging |
| GitHub Actions (CI/CD) | Automated test run on every push/PR to `main` |
| Automated testing | `pytest` + `moto` to mock AWS services, zero-cost, zero-dependency test suite |

## What this demonstrates

- Designing and wiring together four distinct AWS services into one working system, not just standing up one in isolation
- Applying least-privilege IAM as a default habit, not an afterthought
- Writing and running real automated tests against mocked AWS infrastructure before ever touching a real account
- Setting up CI so code quality is enforced automatically going forward
- Debugging real console/tooling friction (auto-closing brackets, mislabeled buttons, flaky simulated input) methodically, verifying each fix before moving on
- End-to-end verification against a live endpoint, not just "it looks right in the console"

## Next steps

- Add a Secrets Manager-stored credential so the Lambda can forward a notification to a Slack webhook on each new lead (rounds out coverage of another commonly-required AWS service)
- Add basic request throttling / a usage plan if this were to front a real public lead form
- Consider a custom domain name mapped to the API Gateway endpoint
- Add a second DynamoDB access pattern (e.g. query by source) with a GSI, to demonstrate index design beyond a single partition key

---

Built by Leonardo Flores, Lionhall Ventures. Repo: [lionhall-serverless-lead-intake](https://github.com/lhflores12/lionhall-serverless-lead-intake)
