from http.client import _is_legal_header_name, _is_illegal_header_value
from django.core.exceptions import ValidationError


def header_name_validator(value):
    if not _is_legal_header_name(value.encode()):
        raise ValidationError("Invalid header name")


def header_value_validator(value):
    if _is_illegal_header_value(value.encode()):
        raise ValidationError("Invalid header value")
