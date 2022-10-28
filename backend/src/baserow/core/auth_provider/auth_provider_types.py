from typing import Any, Dict, Optional

from rest_framework import serializers

from baserow.core.auth_provider.validators import validate_domain
from baserow.core.registry import (
    APIUrlsInstanceMixin,
    CustomFieldsInstanceMixin,
    ImportExportMixin,
    Instance,
    MapAPIExceptionsInstanceMixin,
    ModelInstanceMixin,
)
from baserow.core.utils import set_allowed_attrs

from .models import PasswordAuthProviderModel


class AuthProviderType(
    MapAPIExceptionsInstanceMixin,
    APIUrlsInstanceMixin,
    CustomFieldsInstanceMixin,
    ModelInstanceMixin,
    ImportExportMixin,
    Instance,
):
    def get_login_options(self, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Returns a dictionary containing the login options for this Baserow instance
        to populate the login page accordingly.
        """

        raise NotImplementedError()

    def can_create_new_providers(self):
        """
        Returns True if it's possible to create an authentication provider of this type.
        """

        raise NotImplementedError()

    def before_create(self, user, **values):
        """
        This hook is called before the authentication provider is created.

        :param user: The user that is creating the authentication provider.
        :param values: The values that are used to create the authentication provider.
        """

        pass

    def create(self, **kwargs):
        """
        Creates a new authentication provider instance of the provided type. The
        authentication provider is not saved to the database. The caller is
        responsible for saving the instance.

        :param handler: The handler that is used to manage the authentication providers.
        :return: The created authentication provider instance.
        """

        return self.model_class.objects.create(**kwargs)

    def before_update(self, user, provider, **values):
        """
        This hook is called before the authentication provider is updated.

        :param user: The user that is updating the authentication provider.
        :param provider: The authentication provider that is being updated.
        :param values: The values that are used to update the authentication provider.
        """

        pass

    def update(self, provider, **values):
        """
        Updates the authentication provider instance of the provided type.

        :param provider: The authentication provider that is being updated.
        :param values: The values that are used to update the authentication provider.
        :return: The updated authentication provider instance.
        """

        set_allowed_attrs(values, self.allowed_fields, provider)
        provider.save()
        return provider

    def before_delete(self, user, provider):
        """
        This hook is called before the authentication provider is deleted.

        :param user: The user that is deleting the authentication provider.
        :param provider: The authentication provider that is being deleted.
        """

        pass

    def delete(self, provider):
        """
        Deletes the authentication provider instance of the provided type.

        :param provider: The authentication provider that is being deleted.
        """

        provider.delete()

    def list_providers(self, base_queryset=None):
        """
        Returns a queryset containing all the authentication providers of this type.

        :param base_queryset: The base queryset that can be used to filter the
        """

        if base_queryset is None:
            base_queryset = self.model_class.objects

        return base_queryset.all()

    def export_serialized(self):
        """
        Returns the serialized data for this authentication provider type.
        """

        from baserow.api.auth_provider.serializers import AuthProviderSerializer

        return {
            "type": self.type,
            "can_create_new": self.can_create_new_providers(),
            "auth_providers": [
                self.get_serializer(provider, AuthProviderSerializer).data
                for provider in self.list_providers()
            ],
        }


class PasswordAuthProviderType(AuthProviderType):
    """
    The password authentication provider type is the default authentication provider
    type that is always available. It allows users to login with their email address
    and password.
    """

    type = "password"
    model_class = PasswordAuthProviderModel
    serializer_field_overrides = {
        "domain": serializers.CharField(
            validators=[validate_domain],
            required=False,
            help_text="The email domain (if any) registered with this password provider.",
        ),
        "enabled": serializers.BooleanField(
            help_text="Whether the provider is enabled or not.",
            required=False,
        ),
    }

    def get_login_options(self, **kwargs) -> Optional[Dict[str, Any]]:
        return {}

    def can_create_new_providers(self):
        return False
