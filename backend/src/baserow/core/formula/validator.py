from typing import Any

from django.core.exceptions import ValidationError


def ensure_integer(value: Any) -> int:
    """
    Ensures that the value is an integer or can be converted to an integer.
    Raises a ValidationError if the value is not a valid integer or convertible to an
    integer.

    :param value: The value to ensure as an integer.
    :return: The value as an integer if conversion is successful.
    :raises ValidationError: If the value is not a valid integer or convertible to an
        integer.
    """

    try:
        return int(value)
    except (ValueError, TypeError):
        raise ValidationError(
            "The value must be an integer or convertible to an integer."
        )


def ensure_string(value, allow_empty=True):
    """
    Ensures that the value is a string or try to convert it.

    :param value: The value to ensure as a string.
    :param allow_empty: Whether we should throw an error if `value` is empty.
    :return: The value as a string.
    :raises ValueError: If not allow_empty and the `value` is empty.
    """

    if value is None or value == "":
        if not allow_empty:
            raise ValueError("A valid String is required.")
        return ""
    return str(value)
