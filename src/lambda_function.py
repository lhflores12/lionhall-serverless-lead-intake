import json
import os
import time
import uuid

import boto3
from botocore.exceptions import ClientError

from validation import validate_lead

dynamodb = boto3.resource("dynamodb")


def lambda_handler(event, context):
    table = dynamodb.Table(os.environ["TABLE_NAME"])

    try:
        body = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return _response(400, {"error": "Invalid JSON body"})

    errors = validate_lead(body)
    if errors:
        return _response(400, {"error": "; ".join(errors)})

    lead_id = str(uuid.uuid4())
    item = {
        "leadId": lead_id,
        "name": body["name"],
        "phone": body["phone"],
        "source": body["source"],
        "email": body.get("email", ""),
        "notes": body.get("notes", ""),
        "receivedAt": int(time.time()),
    }

    try:
        table.put_item(Item=item)
    except ClientError as exc:
        # Logged for CloudWatch; never leak the raw AWS error back to the caller.
        print(f"DynamoDB put_item failed: {exc}")
        return _response(500, {"error": "Could not save lead, please try again"})

    return _response(200, {"message": "Lead received", "leadId": lead_id})


def _response(status_code, payload):
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(payload),
    }
