from django.core.exceptions import ValidationError


EMPTY_VALUES = (None, "", b"", [], (), {})


def no_empty_form_values_when_required_validator(value):
    if value_is_empty_for_required_form_field(value):
        raise ValidationError("This field is required.", code="required")


def value_is_empty_for_required_form_field(value):
    return value in EMPTY_VALUES or value is False
