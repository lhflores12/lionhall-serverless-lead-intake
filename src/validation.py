"""Validation helpers for incoming lead-intake payloads.

Kept separate from lambda_function.py on purpose: this module has zero AWS
dependencies, so it can be unit tested in complete isolation (no mocking
boto3, no network, no AWS credentials needed) -- a basic but important
separation-of-concerns habit for production code.
"""
import re

REQUIRED_FIELDS = ["name", "phone", "source"]

# Loosely accepts: 5551234567, 555-123-4567, (555) 123-4567, +1 555 123 4567
PHONE_RE = re.compile(r"^\+?1?[\s.-]?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def validate_lead(body: dict) -> list[str]:
    """Validate a lead payload, returning a list of human-readable errors.

    An empty list means the payload is valid. Checks run in two stages:
    required-field presence first, then format checks on fields that
    exist -- no point validating the shape of a phone number that was
    never provided.
    """
    errors: list[str] = []

    missing = [field for field in REQUIRED_FIELDS if not body.get(field)]
    if missing:
        errors.append(f"Missing required fields: {missing}")
        return errors

    if not PHONE_RE.match(str(body["phone"]).strip()):
        errors.append(f"Invalid phone format: {body['phone']!r}")

    email = body.get("email")
    if email and not EMAIL_RE.match(str(email).strip()):
        errors.append(f"Invalid email format: {email!r}")

    return errors
