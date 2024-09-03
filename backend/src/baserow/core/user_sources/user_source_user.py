from typing import Any, List, Optional, Union

from django.contrib.auth import models as auth_models
from django.db.models.manager import EmptyManager

from rest_framework_simplejwt.settings import api_settings as jwt_settings

from baserow.core.user_sources.constants import (
    EMAIL_CLAIM,
    ROLE,
    USER_SOURCE_CLAIM,
    USERNAME_CLAIM,
)
from baserow.core.user_sources.jwt_token import UserSourceToken


class UserSourceUser:
    """
    A dummy user class modeled after django.contrib.auth.models.AnonymousUser.
    Instances of this class act as stateless user objects.
    """

    # User is always active
    is_active = True

    _groups = EmptyManager(auth_models.Group)
    _user_permissions = EmptyManager(auth_models.Permission)

    def __init__(
        self,
        user_source,
        original_user,
        user_id,
        username,
        email,
        role="",
        is_staff=False,
        is_superuser=False,
        **kwargs,
    ) -> None:
        self.user_source = user_source
        self.original_user = original_user
        self.id = user_id
        self.username = username
        self.email = email
        self.role = role
        self.is_staff = is_staff
        self.is_superuser = is_superuser
        self.extra = kwargs

    def __str__(self) -> str:
        return f"UserSourceUser {self.id}"

    def pk(self) -> Union[int, str]:
        return self.id

    def user_source_id(self):
        return self.user_source.id

    def get_refresh_token(self):
        """
        Return a new refresh token for this user.
        """

        refresh = UserSourceToken()

        # add basic information
        refresh[USER_SOURCE_CLAIM] = str(self.user_source.uid)
        refresh[USERNAME_CLAIM] = str(self.username)
        refresh[EMAIL_CLAIM] = str(self.email)
        refresh[jwt_settings.USER_ID_CLAIM] = self.id
        refresh[ROLE] = self.role

        return refresh

    def update_refresh_token(self, refresh):
        """
        Update the information stored in the token without updating the expiration date.
        """

        updated = False
        if refresh[EMAIL_CLAIM] != str(self.email):
            refresh[EMAIL_CLAIM] = str(self.email)
            updated = True

        if refresh[USERNAME_CLAIM] != str(self.username):
            refresh[USERNAME_CLAIM] = str(self.username)
            updated = True

        return refresh, updated

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, UserSourceUser):
            return NotImplemented
        return self.id == other.id

    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)

    def __hash__(self) -> int:
        return hash(self.id)

    def save(self) -> None:
        raise NotImplementedError("User source users have no DB representation")

    def delete(self) -> None:
        raise NotImplementedError("User source users have no DB representation")

    def set_password(self, raw_password: str) -> None:
        raise NotImplementedError("User source users have no DB representation")

    def check_password(self, raw_password: str) -> None:
        raise NotImplementedError("User source users have no DB representation")

    @property
    def groups(self) -> auth_models.Group:
        return self._groups

    @property
    def user_permissions(self) -> auth_models.Permission:
        return self._user_permissions

    def get_group_permissions(self, obj: Optional[object] = None) -> set:
        return set()

    def get_all_permissions(self, obj: Optional[object] = None) -> set:
        return set()

    def has_perm(self, perm: str, obj: Optional[object] = None) -> bool:
        return False

    def has_perms(self, perm_list: List[str], obj: Optional[object] = None) -> bool:
        return False

    def has_module_perms(self, module: str) -> bool:
        return False

    @property
    def is_anonymous(self) -> bool:
        return False

    @property
    def is_authenticated(self) -> bool:
        return True

    def get_username(self) -> str:
        return self.username

    def get_role(self) -> str:
        return self.role

    def __getattr__(self, attr: str) -> Optional[Any]:
        """This acts as a backup attribute getter for custom attributes."""

        return self.extra.get(attr, None)
