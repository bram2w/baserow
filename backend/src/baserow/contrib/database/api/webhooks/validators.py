from django.core.exceptions import ValidationError as DjangoValidationError

from rest_framework import serializers

from baserow.contrib.database.webhooks.validators import (
    header_name_validator,
    header_value_validator,
    url_validator,
)


def url_validation(value: str) -> str:
    """
    Here we use the custom URL validator.

    :param value: The URL that must be validated.
    :raises serializers.ValidationError: When the provided URL is not valid.
    :return: The provided URL if valid.
    """

    try:
        url_validator(value)
        return value
    except DjangoValidationError as e:
        raise serializers.ValidationError(detail=e.message, code=e.code)


def http_header_validation(headers: dict) -> dict:
    """
    Validates the provided headers. If a key or value is invalid, a validation error
    will be raised.

    :param headers: A dictionary where the key is the header name and the value the
        value.
    :raises serializers.ValidationError: When the provided URL is not valid.
    :return: The provided headers if they are valid.
    """

    for name, value in headers.items():
        try:
            header_name_validator(name)
        except DjangoValidationError:
            raise serializers.ValidationError(
                detail=f"The provided header name {name} is invalid.",
                code="invalid_http_header_name",
            )

        try:
            header_value_validator(value)
        except DjangoValidationError:
            raise serializers.ValidationError(
                detail=f"The provided header value {value} is invalid.",
                code="invalid_http_header_value",
            )

    return headers
