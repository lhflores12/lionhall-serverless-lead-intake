"""
Unit tests for lambda_function.py.

Note on the boto3 stub below: the real AWS SDK (boto3/botocore) is provided
automatically by the Lambda runtime in production, so it's deliberately not
a project dependency here. To unit test the handler without it (and without
real AWS credentials or network access), we register lightweight fake
'boto3' and 'botocore.exceptions' modules in sys.modules before importing
lambda_function. This is a standard pattern for testing AWS Lambda code
in isolation.
"""
import json
import os
import sys
import types
import unittest
from unittest.mock import MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


class _FakeClientError(Exception):
    pass


_fake_botocore_exceptions = types.ModuleType("botocore.exceptions")
_fake_botocore_exceptions.ClientError = _FakeClientError
_fake_botocore = types.ModuleType("botocore")
_fake_botocore.exceptions = _fake_botocore_exceptions

_fake_table = MagicMock()
_fake_resource = MagicMock()
_fake_resource.Table.return_value = _fake_table
_fake_boto3 = types.ModuleType("boto3")
_fake_boto3.resource = MagicMock(return_value=_fake_resource)

sys.modules["boto3"] = _fake_boto3
sys.modules["botocore"] = _fake_botocore
sys.modules["botocore.exceptions"] = _fake_botocore_exceptions

os.environ["TABLE_NAME"] = "test-table"

import lambda_function  # noqa: E402


class TestLambdaHandler(unittest.TestCase):
    def setUp(self):
        _fake_table.reset_mock(return_value=True, side_effect=True)

    @staticmethod
    def _event(body_dict):
        return {"body": json.dumps(body_dict)}

    def test_successful_lead_returns_200_and_writes_to_dynamodb(self):
        event = self._event(
            {
                "name": "Test Lead",
                "phone": "555-123-4567",
                "source": "web",
                "email": "test@example.com",
                "notes": "hi",
            }
        )
        result = lambda_function.lambda_handler(event, None)

        self.assertEqual(result["statusCode"], 200)
        body = json.loads(result["body"])
        self.assertEqual(body["message"], "Lead received")
        self.assertIn("leadId", body)

        _fake_table.put_item.assert_called_once()
        written_item = _fake_table.put_item.call_args.kwargs["Item"]
        self.assertEqual(written_item["name"], "Test Lead")
        self.assertEqual(written_item["leadId"], body["leadId"])

    def test_missing_required_field_returns_400_and_does_not_write(self):
        event = self._event({"phone": "555-123-4567", "source": "web"})
        result = lambda_function.lambda_handler(event, None)

        self.assertEqual(result["statusCode"], 400)
        self.assertIn("name", result["body"])
        _fake_table.put_item.assert_not_called()

    def test_invalid_json_body_returns_400(self):
        event = {"body": "{not valid json"}
        result = lambda_function.lambda_handler(event, None)

        self.assertEqual(result["statusCode"], 400)
        self.assertIn("Invalid JSON", result["body"])

    def test_missing_body_key_defaults_to_empty_payload(self):
        event = {}
        result = lambda_function.lambda_handler(event, None)
        self.assertEqual(result["statusCode"], 400)

    def test_invalid_phone_format_returns_400_and_does_not_write(self):
        event = self._event({"name": "Test", "phone": "abc", "source": "web"})
        result = lambda_function.lambda_handler(event, None)

        self.assertEqual(result["statusCode"], 400)
        _fake_table.put_item.assert_not_called()

    def test_dynamodb_failure_returns_500_not_a_raw_exception(self):
        _fake_table.put_item.side_effect = lambda_function.ClientError("boom")
        event = self._event(
            {"name": "Test", "phone": "555-123-4567", "source": "web"}
        )
        result = lambda_function.lambda_handler(event, None)

        self.assertEqual(result["statusCode"], 500)
        self.assertNotIn("boom", result["body"])  # raw AWS error never leaks out


if __name__ == "__main__":
    unittest.main()
