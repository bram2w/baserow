import unicodedata
from typing import Dict, Optional, Union

from django.contrib.auth.models import AbstractUser

from rest_framework_simplejwt.tokens import AccessToken, RefreshToken


def normalize_email_address(email):
    """
    Normalizes an email address by stripping the whitespace, converting to lowercase
    and by normalizing the unicode.

    :param email: The email address that needs to be normalized.
    :type email: str
    :return: The normalized email address.
    :rtype: str
    """

    return unicodedata.normalize("NFKC", email).strip().lower()


def generate_session_tokens_for_user(
    user: AbstractUser, include_refresh_token: bool = False
) -> Dict[str, str]:
    """
    Generates a new access and refresh token (if requested) for the given user.

    :param user: The user for which the tokens must be generated.
    :param include_refresh_token: Whether or not a refresh token must be included.
    :return: A dictionary with the access and refresh token.
    """

    access_token = AccessToken.for_user(user)
    refresh_token = RefreshToken.for_user(user) if include_refresh_token else None
    return prepare_user_tokens_payload(access_token, refresh_token)


def prepare_user_tokens_payload(
    access_token: Union[AccessToken, str],
    refresh_token: Optional[Union[RefreshToken, str]] = None,
) -> Dict[str, str]:
    """
    Generates a new access and refresh token (if requested) for the given user.
    For backward compatibility the access token is also returned under the key
    `token` (deprecated).

    :param access_token: The access token that must be returned.
    :param refresh_token: The refresh token that must be returned.
    :return: A dictionary with the access and refresh token.
    """

    session_tokens = {
        "token": str(access_token),
        "access_token": str(access_token),
    }

    if refresh_token:
        session_tokens["refresh_token"] = str(refresh_token)

    return session_tokens
