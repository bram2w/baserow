import uuid
from urllib.parse import parse_qs

import jwt
from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth import get_user_model
from rest_framework_jwt.settings import api_settings

jwt_get_username_from_payload = api_settings.JWT_PAYLOAD_GET_USERNAME_HANDLER
jwt_decode_token = api_settings.JWT_DECODE_HANDLER


@database_sync_to_async
def get_user(token):
    """
    Selects a user related to the provided JWT token. If the token is invalid or if the
    user does not exist then None is returned.

    :param token: The JWT token for which the user must be fetched.
    :type token: str
    :return: The user related to the JWT token.
    :rtype: User or None
    """

    try:
        payload = jwt_decode_token(token)
    except jwt.InvalidTokenError:
        return

    User = get_user_model()
    username = jwt_get_username_from_payload(payload)

    if not username:
        return

    try:
        user = User.objects.get_by_natural_key(username)
    except User.DoesNotExist:
        return

    if not user.is_active:
        return

    return user


class JWTTokenAuthMiddleware(BaseMiddleware):
    """
    The auth middleware adds a user object to the scope if a valid JWT token is
    provided via the GET parameters when requesting the web socket. It also adds a
    unique web socket id for future identification.
    """

    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        get = parse_qs(scope["query_string"].decode("utf8"))
        scope["user"] = None
        scope["web_socket_id"] = None

        jwt_token = get.get("jwt_token")

        if jwt_token:
            scope["user"] = await get_user(jwt_token[0])
            scope["web_socket_id"] = str(uuid.uuid4())

        return await self.inner(scope, receive, send)
