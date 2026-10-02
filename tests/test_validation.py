import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from validation import validate_lead  # noqa: E402


class TestValidateLead(unittest.TestCase):
    def test_valid_payload_has_no_errors(self):
        body = {
            "name": "Test Lead",
            "phone": "555-123-4567",
            "source": "web",
            "email": "a@b.com",
        }
        self.assertEqual(validate_lead(body), [])

    def test_missing_single_field(self):
        body = {"name": "Test Lead", "source": "web"}
        errors = validate_lead(body)
        self.assertTrue(any("phone" in e for e in errors))

    def test_missing_multiple_fields_lists_all_of_them(self):
        body = {}
        errors = validate_lead(body)
        self.assertEqual(len(errors), 1)
        self.assertIn("name", errors[0])
        self.assertIn("phone", errors[0])
        self.assertIn("source", errors[0])

    def test_invalid_phone_format(self):
        body = {"name": "Test", "phone": "not-a-phone", "source": "web"}
        errors = validate_lead(body)
        self.assertTrue(any("phone" in e.lower() for e in errors))

    def test_invalid_email_format_when_provided(self):
        body = {
            "name": "Test",
            "phone": "555-123-4567",
            "source": "web",
            "email": "not-an-email",
        }
        errors = validate_lead(body)
        self.assertTrue(any("email" in e.lower() for e in errors))

    def test_email_is_optional(self):
        body = {"name": "Test", "phone": "555-123-4567", "source": "web"}
        self.assertEqual(validate_lead(body), [])

    def test_accepts_common_phone_formats(self):
        for phone in [
            "5551234567",
            "555-123-4567",
            "(555) 123-4567",
            "+1 555 123 4567",
        ]:
            body = {"name": "Test", "phone": phone, "source": "web"}
            self.assertEqual(validate_lead(body), [], f"Should accept {phone!r}")


if __name__ == "__main__":
    unittest.main()
