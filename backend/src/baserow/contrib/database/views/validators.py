from django.core.exceptions import ValidationError


EMPTY_VALUES = (None, "", b"", [], (), {}, False)


def required_validator(value):
    if value in EMPTY_VALUES:
        raise ValidationError("This field is required.", code="required")
