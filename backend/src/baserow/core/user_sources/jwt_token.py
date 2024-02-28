from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
from rest_framework_simplejwt.utils import datetime_from_epoch

from baserow.core.user.handler import UserHandler


class UserSourceAccessToken(AccessToken):
    token_type = "access_user_source"  # nosec b105


class UserSourceToken(RefreshToken):
    """
    Basically the same as the RefreshToken but with custom methods for token
    blacklisting.
    """

    token_type = "refresh_user_source"  # nosec b105
    access_token_class = UserSourceAccessToken

    def verify(self, *args, **kwargs) -> None:
        self.check_blacklist()
        super().verify(*args, **kwargs)  # type: ignore

    def check_blacklist(self) -> bool:
        """
        Checks if this token is present in the token blacklist.  Raises
        `TokenError` if so.
        """

        if UserHandler().refresh_token_is_blacklisted(self):
            raise TokenError("Token is blacklisted")

    def blacklist(self):
        """Blacklist the current token so it can't be used anymore."""

        expires_at = datetime_from_epoch(self["exp"])
        UserHandler().blacklist_refresh_token(self, expires_at)
