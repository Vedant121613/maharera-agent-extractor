"""
Data validation helpers.
"""

import re

_EMAIL_RE   = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
_PINCODE_RE = re.compile(r"^\d{6}$")
_PHONE_RE   = re.compile(r"^[+\d\s\-().]{7,20}$")


def validate_email(value: str) -> bool:
    return bool(_EMAIL_RE.match(value.strip()))


def validate_pincode(value: str) -> bool:
    return bool(_PINCODE_RE.match(value.strip()))


def validate_phone(value: str) -> bool:
    return bool(_PHONE_RE.match(value.strip()))


def clean_text(value: str) -> str:
    """Strip whitespace and collapse internal spaces."""
    return re.sub(r"\s+", " ", value).strip()
