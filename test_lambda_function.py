import importlib
import json
import os

import boto3
from moto import mock_aws

os.environ.setdefault('AWS_DEFAULT_REGION', 'us-east-1')
os.environ['TABLE_NAME'] = 'TestLeads'


def _create_table():
    client = boto3.client('dynamodb', region_name='us-east-1')
    client.create_table(
        TableName='TestLeads',
        KeySchema=[{'AttributeName': 'leadId', 'KeyType': 'HASH'}],
        AttributeDefinitions=[{'AttributeName': 'leadId', 'AttributeType': 'S'}],
        BillingMode='PAY_PER_REQUEST',
    )


@mock_aws
def test_valid_lead_creates_item():
    _create_table()
    import lambda_function
    importlib.reload(lambda_function)

    event = {'body': json.dumps({'name': 'Jane Doe', 'phone': '555-1234', 'source': 'test'})}
    result = lambda_function.lambda_handler(event, None)

    assert result['statusCode'] == 200
    body = json.loads(result['body'])
    assert 'leadId' in body


@mock_aws
def test_missing_required_fields_returns_400():
    _create_table()
    import lambda_function
    importlib.reload(lambda_function)

    event = {'body': json.dumps({'name': 'Jane Doe'})}
    result = lambda_function.lambda_handler(event, None)

    assert result['statusCode'] == 400
    body = json.loads(result['body'])
    assert 'error' in body


@mock_aws
def test_invalid_json_returns_400():
    _create_table()
    import lambda_function
    importlib.reload(lambda_function)

    event = {'body': 'not json'}
    result = lambda_function.lambda_handler(event, None)

    assert result['statusCode'] == 400
