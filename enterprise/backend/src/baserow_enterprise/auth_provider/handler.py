from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple, Type

from django.contrib.auth.models import AbstractUser
from django.db import connection

from psycopg2 import sql

from baserow.core.action.registries import action_type_registry
from baserow.core.actions import AcceptGroupInvitationActionType
from baserow.core.auth_provider.auth_provider_types import AuthProviderType
from baserow.core.auth_provider.exceptions import AuthProviderModelNotFound
from baserow.core.auth_provider.models import AuthProviderModel
from baserow.core.handler import CoreHandler
from baserow.core.registries import auth_provider_type_registry
from baserow.core.user.actions import CreateUserActionType, SignInUserActionType
from baserow.core.user.exceptions import UserNotFound
from baserow.core.user.handler import UserHandler
from baserow_enterprise.auth_provider.exceptions import (
    CannotCreateAuthProvider,
    CannotDeleteAuthProvider,
    CannotDisableLastAuthProvider,
    DifferentAuthProvider,
)

SpecificAuthProviderModel = Type[AuthProviderModel]


@dataclass
class UserInfo:
    email: str
    name: str
    language: Optional[str] = None
    group_invitation_token: Optional[str] = None


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

        if not auth_provider_type.can_create_new_providers():
            raise CannotCreateAuthProvider()
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

        enabled_next = values.get("enabled", None)
        if enabled_next is False:
            another_enabled = (
                AuthProviderModel.objects.filter(enabled=True)
                .exclude(id=auth_provider.id)
                .exists()
            )
            if not another_enabled:
                raise CannotDisableLastAuthProvider()

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
        if not auth_provider_type.can_delete_existing_providers():
            raise CannotDeleteAuthProvider()
        another_enabled = (
            AuthProviderModel.objects.filter(enabled=True)
            .exclude(id=auth_provider.id)
            .exists()
        )
        if not another_enabled:
            raise CannotDisableLastAuthProvider()
        auth_provider_type.before_delete(user, auth_provider)
        auth_provider_type.delete(auth_provider)

    @classmethod
    def get_or_create_user_and_sign_in_via_auth_provider(
        cls, user_info: UserInfo, auth_provider: Type[AuthProviderModel]
    ) -> Tuple[AbstractUser, bool]:
        """
        Gets from the database if present or creates a user if not, based on the
        user info that was received from the identity provider.

        :param user_info: A dataclass containing the user info that can be sent
            to the UserHandler().create_user() method.
        :param auth_provider: The authentication provider that was used to
            authenticate the user.
        :raises DeactivatedUserException: If the user exists but has been
            disabled from an admin.
        :return: The user that was created or retrieved and a boolean flag set
            to True if the user has been created, False otherwise.
        """

        user_handler = UserHandler()
        try:
            user = user_handler.get_active_user(email=user_info.email)

            is_original_provider = auth_provider.users.filter(id=user.id).exists()
            if not is_original_provider:
                raise DifferentAuthProvider()

            action_type_registry.get(SignInUserActionType.type).do(user, auth_provider)

            if user_info.group_invitation_token:
                core_handler = CoreHandler()
                invitation = core_handler.get_group_invitation_by_token(
                    user_info.group_invitation_token
                )
                action_type_registry.get(AcceptGroupInvitationActionType.type).do(
                    user, invitation
                )

            created = False
        except UserNotFound:
            user = action_type_registry.get(CreateUserActionType.type).do(
                name=user_info.name,
                email=user_info.email,
                password=None,
                language=user_info.language,
                group_invitation_token=user_info.group_invitation_token,
                auth_provider=auth_provider,
            )
            created = True

        return user, created

    @staticmethod
    def get_next_provider_id() -> int:
        """
        Returns the next provider id so that the callback URL
        can be guessed before the provided is created.
        """

        with connection.cursor() as cursor:
            cursor.execute(
                sql.SQL("SELECT last_value + 1 from {table_id_seq};").format(
                    table_id_seq=sql.Identifier(
                        f"{AuthProviderModel._meta.db_table}_id_seq"
                    )
                )
            )
            return int(cursor.fetchone()[0])
