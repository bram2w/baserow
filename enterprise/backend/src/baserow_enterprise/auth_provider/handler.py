from dataclasses import dataclass
from typing import Any, Dict, Optional, Type

from django.contrib.auth.models import AbstractUser
from django.db import connection, transaction

from baserow.core.auth_provider.auth_provider_types import AuthProviderType
from baserow.core.auth_provider.exceptions import AuthProviderModelNotFound
from baserow.core.auth_provider.models import AuthProviderModel
from baserow.core.registries import auth_provider_type_registry
from baserow.core.user.exceptions import UserNotFound
from baserow.core.user.handler import UserHandler
from baserow_enterprise.auth_provider.exceptions import DifferentAuthProvider

SpecificAuthProviderModel = Type[AuthProviderModel]


@dataclass
class UserInfo:
    email: str
    name: str
    language: Optional[str] = None


class AuthProviderHandler:
    @classmethod
    def get_auth_provider(cls, auth_provider_id: int) -> SpecificAuthProviderModel:
        """
        Returns the authentication provider with the provided id.

        :param auth_provider_id: The id of the authentication provider.
        :raises AuthProviderModelNotFound: When the authentication provider does not
            exist.
        :return: The requested authentication provider.
        """

        try:
            return AuthProviderModel.objects.get(id=auth_provider_id).specific
        except AuthProviderModel.DoesNotExist:
            raise AuthProviderModelNotFound()

    @classmethod
    def create_auth_provider(
        cls,
        user: AbstractUser,
        auth_provider_type: Type[AuthProviderType],
        **values: Dict[str, Any],
    ) -> SpecificAuthProviderModel:
        """
        Creates a new authentication provider of the provided type.

        :param user: The user that is creating the authentication provider.
        :param auth_provider_type: The type of the authentication provider.
        :param values: The values that should be set on the authentication provider.
        :return: The created authentication provider.
        """

        auth_provider_type.before_create(user, **values)
        return auth_provider_type.create(**values)

    @classmethod
    def update_auth_provider(
        cls,
        user: AbstractUser,
        auth_provider: SpecificAuthProviderModel,
        **values: Dict[str, Any],
    ) -> SpecificAuthProviderModel:
        """
        Updates the authentication provider with the provided id.

        :param user: The user that is updating the authentication provider.
        :param auth_provider: The authentication provider that should be updated.
        :param values: The values that should be set on the authentication provider.
        :return: The updated authentication provider.
        """

        auth_provider_type = auth_provider_type_registry.get_by_model(auth_provider)
        auth_provider_type.before_update(user, auth_provider, **values)
        return auth_provider_type.update(auth_provider, **values)

    @classmethod
    def delete_auth_provider(cls, user: AbstractUser, auth_provider: AuthProviderModel):
        """
        Deletes the authentication provider with the provided id. If the user is not
        allowed to delete the authentication provider then an error will be raised.

        :param user: The user that is deleting the authentication provider.
        :param auth_provider: The authentication provider that should be deleted.
        """

        auth_provider_type = auth_provider_type_registry.get_by_model(auth_provider)
        auth_provider_type.before_delete(user, auth_provider)
        auth_provider_type.delete(auth_provider)

    @classmethod
    def get_or_create_user_and_sign_in_via_auth_provider(
        cls, user_info: UserInfo, auth_provider: Type[AuthProviderModel]
    ) -> AbstractUser:
        """
        Gets from the database if present or creates a user if not, based on the
        user info that was received from the identity provider.

        :param user_info: A dataclass containing the user info that can be sent
            to the UserHandler().create_user() method.
        :param auth_provider: The authentication provider that was used to
            authenticate the user.
        :raises UserAlreadyExists: When the user already exists but has been
            disabled from an admin.
        :return: The user that was created or updated.
        """

        user_handler = UserHandler()
        try:
            user = user_handler.get_active_user(email=user_info.email)

            is_original_provider = auth_provider.users.filter(id=user.id).exists()
            if not is_original_provider:
                raise DifferentAuthProvider()
        except UserNotFound:
            with transaction.atomic():
                user = user_handler.create_user(
                    email=user_info.email,
                    name=user_info.name,
                    language=user_info.language,
                    password=None,
                    auth_provider=auth_provider,
                )

        return user

    @staticmethod
    def get_next_provider_id() -> int:
        """
        Returns the next provider id so that the callback URL
        can be guessed before the provided is created.
        """

        with connection.cursor() as cursor:
            cursor.execute("SELECT last_value + 1 FROM core_authprovidermodel_id_seq;")
            row = cursor.fetchone()
            return int(row[0])
