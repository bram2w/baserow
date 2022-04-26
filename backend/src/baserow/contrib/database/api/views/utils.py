from typing import Optional

from django.conf import settings
from rest_framework.request import Request


def get_public_view_authorization_token(request: Request) -> Optional[str]:
    """
    Returns the permission token to access a public view, if any.

    :param request: The request.
    :return: The public view permission token.
    """

    auth_header = request.headers.get(settings.PUBLIC_VIEW_AUTHORIZATION_HEADER, None)
    try:
        _, token = auth_header.split(" ", 1)
    except (AttributeError, ValueError):
        return None
    return token
