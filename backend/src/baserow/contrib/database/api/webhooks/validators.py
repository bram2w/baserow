from urllib.parse import urlparse

from advocate.addrvalidator import AddrValidator
from advocate.connection import (
    UnacceptableAddressException,
    validating_create_connection,
)

from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError

from rest_framework import serializers

from baserow.contrib.database.webhooks.validators import (
    header_name_validator,
    header_value_validator,
)


def url_validation(value: str) -> str:
    """
    This is a custom url validation, needed in order to make sure that users will not
    enter a url which could be in the network of where baserow is running. It makes
    use of the advocate libraries own address validation.

    :param value: The URL that must be validated.
    :raises serializers.ValidationError: When the provided URL is not valid.
    :return: The provided URL if valid.
    """

    # in case we run the develop server we want to allow every url.
    if settings.DEBUG is True:
        return value

    url = urlparse(value)

    # in case the user does not provide a port we assume 80 if it is a
    # http url or 443 otherwise.
    if url.port is None:
        if url.scheme == "http":
            port = 80
        else:
            port = 443
    else:
        port = url.port

    addr_validator = AddrValidator()

    try:
        validating_create_connection((url.hostname, port), validator=addr_validator)
        return value
    except UnacceptableAddressException:
        raise serializers.ValidationError(detail="Not a valid url", code="invalid_url")


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
