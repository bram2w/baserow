from http.client import _is_legal_header_name, _is_illegal_header_value
from urllib.parse import urlparse

from django.conf import settings
from django.core.exceptions import ValidationError

from advocate.addrvalidator import AddrValidator
from advocate.connection import (
    UnacceptableAddressException,
    validating_create_connection,
)


def url_validator(value):
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

    try:
        url = urlparse(value)
        # Reading an invalid port can raise a ValueError exception
        port = url.port
    except ValueError:
        raise ValidationError("Invalid URL")

    # in case the user does not provide a port we assume 80 if it is a
    # http url or 443 otherwise.
    if port is None:
        if url.scheme == "http":
            port = 80
        else:
            port = 443

    addr_validator = AddrValidator()

    try:
        validating_create_connection((url.hostname, port), validator=addr_validator)
        return value
    except UnacceptableAddressException:
        raise ValidationError("Invalid URL")


def header_name_validator(value):
    if not _is_legal_header_name(value.encode()):
        raise ValidationError("Invalid header name")


def header_value_validator(value):
    if _is_illegal_header_value(value.encode()):
        raise ValidationError("Invalid header value")
