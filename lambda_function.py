import json
import os
import time
import uuid
import boto3

dynamodb = boto3.resource('dynamodb')

REQUIRED_FIELDS = ['name', 'phone', 'source']


def lambda_handler(event, context):
    table = dynamodb.Table(os.environ['TABLE_NAME'])

    try:
        body = json.loads(event.get('body') or '{}')
    except json.JSONDecodeError:
        return _response(400, {'error': 'Invalid JSON body'})

    missing = [field for field in REQUIRED_FIELDS if not body.get(field)]
    if missing:
        return _response(400, {'error': f'Missing required fields: {missing}'})

    lead_id = str(uuid.uuid4())
    item = {
        'leadId': lead_id,
        'name': body['name'],
        'phone': body['phone'],
        'source': body['source'],
        'email': body.get('email', ''),
        'notes': body.get('notes', ''),
        'receivedAt': int(time.time()),
    }

    table.put_item(Item=item)

    return _response(200, {'message': 'Lead received', 'leadId': lead_id})


def _response(status_code, payload):
    return {
        'statusCode': status_code,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps(payload),
    }
