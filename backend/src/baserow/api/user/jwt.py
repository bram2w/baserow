from typing import Optional, Type

from django.contrib.auth.models import AbstractUser

from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework_simplejwt.settings import api_settings as jwt_settings
from rest_framework_simplejwt.tokens import AccessToken, Token


def get_user_from_token(
    token: str,
    token_class: Optional[Type[Token]] = None,
    check_if_refresh_token_is_blacklisted: Optional[bool] = False,
) -> AbstractUser:
    """
    Returns the active user that is associated with the given JWT token.

    :param token: The JWT token string
    :param token_class: The token class that must be used to decode the token.
    :param check_if_refresh_token_is_blacklisted: If True, then it check whether the
        provided token is blacklisted.
    :raises InvalidToken: If the token is invalid or if the user does not exist
        or has been disabled.
    :return: The user that is associated with the token
    """

    from baserow.core.user.handler import UserHandler, UserNotFound

    TokenClass = token_class or AccessToken
    try:
        token = TokenClass(token)
        user_id = token[jwt_settings.USER_ID_CLAIM]
    except KeyError:
        raise InvalidToken("Token contained no recognizable user identification")

    if (
        check_if_refresh_token_is_blacklisted
        and UserHandler().refresh_token_is_blacklisted(token)
    ):
        raise InvalidToken("Token is blacklisted.")

    try:
        # Prevent users to renew their token during the grace time.
        # This force a user to login again to have a new token
        # and stops the deletion process.
        user = UserHandler().get_active_user(
            user_id, exclude_users_scheduled_to_be_deleted=True
        )
    except UserNotFound:
        # It could happen if the user was deleted after the token was issued.
        raise InvalidToken("User does not exist.")

    if not user.profile.is_jwt_token_valid(token):
        raise InvalidToken("Token is invalidated.")

    if not user.is_active:
        raise InvalidToken("User is not active.")

    return user
