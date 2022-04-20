import re
from typing import Any

from django.conf import settings
from django.contrib.auth.models import AbstractUser

from baserow.api.exceptions import InvalidClientSessionIdAPIException

UNTRUSTED_CLIENT_SESSION_ID_USER_ATTR = "untrusted_client_session_id"


def _raise_if_not_valid_untrusted_client_session_id(value: Any):
    is_valid = (
        isinstance(value, str)
        and re.match(r"^[0-9a-zA-Z-]+$", value)
        and len(value) <= settings.MAX_CLIENT_SESSION_ID_LENGTH
    )
    if not is_valid:
        raise InvalidClientSessionIdAPIException()


def set_untrusted_client_session_id_from_request_or_raise_if_invalid(
    user: AbstractUser, request
):
    """
    Extracts the untrusted client session id from the requests headers and sets it
    on a custom attr on the user object for later retrieval. If the header is not set
    then nothing will be set. If the header is set but has an invalid value then an
    APIException will be raised.

    :param user: The user to set the client id attr on.
    :param request: The request containing the headers to check.
    """

    session_id = request.headers.get(settings.CLIENT_SESSION_ID_HEADER, None)
    if session_id is not None:
        _raise_if_not_valid_untrusted_client_session_id(session_id)
        set_untrusted_client_session_id(user, session_id)


def set_untrusted_client_session_id(user: AbstractUser, session_id: str):
    setattr(user, UNTRUSTED_CLIENT_SESSION_ID_USER_ATTR, session_id)


def get_untrusted_client_session_id(user: AbstractUser):
    return getattr(user, UNTRUSTED_CLIENT_SESSION_ID_USER_ATTR, None)
