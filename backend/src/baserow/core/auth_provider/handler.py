from typing import TYPE_CHECKING, Any, Dict, Iterable, Optional

from django.contrib.auth.models import AbstractUser
from django.db.models import QuerySet

from baserow.core.auth_provider.exceptions import AuthProviderModelNotFound
from baserow.core.auth_provider.models import (
    AuthProviderModel,
    PasswordAuthProviderModel,
)
from baserow.core.auth_provider.types import AuthProviderModelSubClass
from baserow.core.db import specific_iterator

if TYPE_CHECKING:
    from baserow.core.auth_provider.auth_provider_types import BaseAuthProviderType


class BaseAuthProviderHandler:
    """
    Base handler to manage auth providers.
    """

    # Base django model class to use with this handler
    base_class: AuthProviderModelSubClass

    @classmethod
    def get_auth_provider_by_id(
        cls, auth_provider_id: int, base_queryset: Optional[QuerySet] = None
    ) -> AuthProviderModelSubClass:
        """
        Returns the authentication provider with the provided id.

        :param auth_provider_id: The id of the authentication provider.
        :param base_queryset: if provided, used as base queryset to build the final
          queryset.
        :raises AuthProviderModelNotFound: When the authentication provider does not
            exist.
        :return: The requested authentication provider.
        """

        queryset = (
            base_queryset if base_queryset is not None else cls.base_class.objects.all()
        )

        try:
            return queryset.get(id=auth_provider_id).specific
        except cls.base_class.DoesNotExist as exc:
            raise AuthProviderModelNotFound() from exc

    @classmethod
    def list_all_auth_providers(
        cls,
        base_queryset: Optional[QuerySet] = None,
        specific: bool = True,
    ) -> Iterable[AuthProviderModelSubClass]:
        """
        Returns all auth providers of the given base class.

        :param base_queryset: if provided, used as base queryset to build the final
          queryset.
        :param specific: return specific instances if True.
        :return: an iterable of auth providers.
        """

        queryset = (
            base_queryset if base_queryset is not None else cls.base_class.objects.all()
        )

        if specific:
            queryset = queryset.select_related("content_type")
            return specific_iterator(queryset)
        else:
            return queryset

    @classmethod
    def create_auth_provider(
        cls,
        user: AbstractUser,
        auth_provider_type: "BaseAuthProviderType",
        **values: Dict[str, Any],
    ) -> AuthProviderModelSubClass:
        """
        Creates a new authentication provider of the provided type.

        :param user: The user that is creating the authentication provider.
        :param auth_provider_type: The type of the authentication provider.
        :param values: The values that should be set on the authentication provider.
        :return: The created authentication provider.
        """

        auth_provider_type.before_create(user, **values)

        prepared_values = auth_provider_type.prepare_values(values, user)

        created = auth_provider_type.create(**prepared_values)

        auth_provider_type.after_create(user, created)

        return created

    @classmethod
    def update_auth_provider(
        cls,
        user: AbstractUser,
        auth_provider: AuthProviderModelSubClass,
        **values: Dict[str, Any],
    ) -> AuthProviderModelSubClass:
        """
        Updates the authentication provider with the provided id.

        :param user: The user that is updating the authentication provider.
        :param auth_provider: The authentication provider that should be updated.
        :param values: The values that should be set on the authentication provider.
        :return: The updated authentication provider.
        """

        auth_provider.get_type().before_update(user, auth_provider, **values)

        prepared_values = auth_provider.get_type().prepare_values(
            values, user, instance=auth_provider
        )

        updated = auth_provider.get_type().update(auth_provider, **prepared_values)

        auth_provider.get_type().after_update(user, auth_provider)

        return updated

    @classmethod
    def delete_auth_provider(
        cls, user: AbstractUser, auth_provider: AuthProviderModelSubClass
    ):
        """
        Deletes the authentication provider with the provided id. If the user is not
        allowed to delete the authentication provider then an error will be raised.

        :param user: The user that is deleting the authentication provider.
        :param auth_provider: The authentication provider that should be deleted.
        """

        auth_provider.get_type().before_delete(user, auth_provider)

        auth_provider.get_type().delete(auth_provider)

        auth_provider.get_type().after_delete(user, auth_provider)


class AuthProviderHandler(BaseAuthProviderHandler):
    base_class = AuthProviderModel


class PasswordProviderHandler:
    @classmethod
    def get(cls) -> PasswordAuthProviderModel:
        """
        Returns the password provider

        :return: The one and only password provider.
        """

        obj, created = PasswordAuthProviderModel.objects.get_or_create()
        return obj
