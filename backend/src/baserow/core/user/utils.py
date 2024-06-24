import unicodedata
from dataclasses import asdict, dataclass
from typing import Dict, Optional, Union

from django.contrib.auth.models import AbstractUser
from django.core.signing import TimestampSigner

from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from baserow.core.utils import generate_hash


@dataclass
class UserSessionPayload:
    user_id: int
    token_hash: str


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
    user: AbstractUser,
    include_refresh_token: bool = False,
    verified_email_claim: Optional[str] = None,
) -> Dict[str, str]:
    """
    Generates a new access and refresh token (if requested) for the given user.

    :param user: The user for which the tokens must be generated.
    :param include_refresh_token: Whether or not a refresh token must be included.
    :param verified_email_claim: Optionally stores which authentication
        method was used.
    :return: A dictionary with the access and refresh token.
    """

    access_token = AccessToken.for_user(user)
    refresh_token = RefreshToken.for_user(user) if include_refresh_token else None

    if refresh_token and verified_email_claim is not None:
        refresh_token["verified_email_claim"] = verified_email_claim

    return prepare_user_tokens_payload(user.id, access_token, refresh_token)


def sign_user_session(user_id: int, refresh_token: str) -> str:
    """
    Signs the given user session using the Django signing backend.
    This session can be used to verify the user's identity in a cookie and will
    be valid for the same time of the refresh_token lifetime or until the user
    logs out (blacklisting the token).

    NOTE: Don't use this payload to authenticate users in the API, especially
    for operations that can change the user's state, to avoid CSRF attacks.
    This payload is only meant to be used to verify the user's identity in a
    cookie for GET requests when the Authorization header is not available.

    :param user_id: The user id that must be signed.
    :param refresh_token: The refresh token defining the session. An hash of this
        token will be stored in the session to keep it secure.
    :return: The signed user id.
    """

    return TimestampSigner().sign_object(
        asdict(UserSessionPayload(str(user_id), generate_hash(refresh_token)))
    )


def prepare_user_tokens_payload(
    user_id: int,
    access_token: Union[AccessToken, str],
    refresh_token: Optional[Union[RefreshToken, str]] = None,
) -> Dict[str, str]:
    """
    Generates a new access and refresh token (if requested) for the given user.
    For backward compatibility the access token is also returned under the key
    `token` (deprecated).

    :param user_id: The user id for which the tokens must be generated.
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
        session_tokens["user_session"] = sign_user_session(user_id, str(refresh_token))

    return session_tokens
