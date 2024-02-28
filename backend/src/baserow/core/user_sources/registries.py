import uuid
from abc import ABC, abstractmethod
from typing import Any, Dict, Iterable, Optional, Type, TypeVar

from django.contrib.auth.models import AbstractUser

from baserow.core.app_auth_providers.handler import AppAuthProviderHandler
from baserow.core.app_auth_providers.registries import app_auth_provider_type_registry
from baserow.core.integrations.handler import IntegrationHandler
from baserow.core.registry import (
    CustomFieldsInstanceMixin,
    CustomFieldsRegistryMixin,
    EasyImportExportMixin,
    Instance,
    ModelInstanceMixin,
    ModelRegistryMixin,
    Registry,
)
from baserow.core.user_sources.user_source_user import UserSourceUser

from .models import UserSource
from .types import UserSourceDictSubClass, UserSourceSubClass


class UserSourceType(
    ModelInstanceMixin[UserSource],
    EasyImportExportMixin[UserSourceSubClass],
    CustomFieldsInstanceMixin,
    Instance,
    ABC,
):
    SerializedDict: Type[UserSourceDictSubClass]
    parent_property_name = "application"
    id_mapping_name = "user_sources"

    """
    An user_source type define a specific user_source with a given external service.
    """

    def enhance_queryset(self, queryset):
        """
        Allow to enhance the queryset when querying the user_source mainly to improve
        performances.
        """

        return queryset

    def prepare_values(
        self,
        values: Dict[str, Any],
        user: AbstractUser,
        instance: Optional[UserSourceSubClass] = None,
    ) -> Dict[str, Any]:
        """
        The prepare_values hook gives the possibility to change the provided values
        that just before they are going to be used to create or update the instance. For
        example if an ID is provided, it can be converted to a model instance. Or to
        convert a certain date string to a date object. It's also an opportunity to add
        specific validations.

        :param values: The provided values.
        :param user: The user on whose behalf the change is made.
        :param instance: The current instance if it exists.
        :return: The updated values.
        """

        # We load the actual integration object
        if "integration_id" in values:
            integration_id = values.pop("integration_id")
            if integration_id is not None:
                integration = IntegrationHandler().get_integration(integration_id)
                values["integration"] = integration
            else:
                values["integration"] = None

        return values

    def after_create(self, user, user_source, values):
        """
        Add the auth providers.
        """

        if "auth_providers" in values:
            for ap in values["auth_providers"]:
                ap_type = app_auth_provider_type_registry.get(ap["type"])
                ap_type.check_user_source_compatibility(user_source)
                AppAuthProviderHandler.create_app_auth_provider(
                    user, ap_type, user_source, **ap
                )

    def after_update(self, user, user_source, values):
        """
        Recreate the auth providers.
        """

        if "auth_providers" in values:
            user_source.auth_providers.all().delete()
            self.after_create(user, user_source, values)

    def serialize_property(self, instance: UserSource, prop_name: str):
        if prop_name == "order":
            return str(instance.order)

        if prop_name == "auth_providers":
            return [
                ap.get_type().export_serialized(ap)
                for ap in AppAuthProviderHandler.list_app_auth_providers_for_user_source(
                    instance
                )
            ]

        return super().serialize_property(instance, prop_name)

    def deserialize_property(
        self,
        prop_name: str,
        value: Any,
        id_mapping: Dict[str, Dict[int, int]],
        **kwargs,
    ) -> Any:
        if prop_name == "integration_id":
            return id_mapping["integrations"][value]

        if prop_name == "uid":
            # If the uid is already used then we need to update it to ensure the
            # uniqueness
            if UserSource.objects.filter(uid=value).exists():
                return uuid.uuid4().hex
            else:
                return value

        return super().deserialize_property(prop_name, value, id_mapping, **kwargs)

    def import_serialized(
        self,
        parent: Any,
        serialized_values: Dict[str, Any],
        id_mapping: Dict[str, Dict[int, int]],
        **kwargs,
    ) -> UserSourceSubClass:
        """
        Handles the auth provider import.
        """

        auth_providers = serialized_values.pop("auth_providers", [])

        created_user_source = super().import_serialized(
            parent, serialized_values, id_mapping, **kwargs
        )

        for auth_provider in auth_providers:
            auth_provider_type = app_auth_provider_type_registry.get(
                auth_provider["type"]
            )
            auth_provider_type.import_serialized(
                created_user_source, auth_provider, id_mapping
            )

        return created_user_source

    @abstractmethod
    def gen_uid(self, user_source):
        """
        Should generate a new UID given a user_source. This UID must be different if
        the configuration has changed substantially and the current user tokens need
        to be invalidated.
        """

    @abstractmethod
    def list_users(
        self, user_source: UserSource, count: int = 5, search: str = ""
    ) -> Iterable[UserSourceUser]:
        """
        Returns a list of users for this user source.

        :param user_source: The user source instance.
        :param count: The number of user we want.
        :param search: A search term to filter the users.
        :return: An iterable of users.
        """

    @abstractmethod
    def get_user(self, user_source: UserSource, **kwargs) -> Optional[UserSourceUser]:
        """
        Returns a user given some args.

        :param user_source: The user source used to get the user.
        :param kwargs: Keyword arguments to get the user.
        :return: A user instance if any found with the given parameters.
        """

    @abstractmethod
    def authenticate(self, user_source: UserSource, **kwargs) -> UserSourceUser:
        """
        Authenticates using the given credentials. It uses the password auth provider.

        :param user_source: The user source used to authenticate the user.
        :param kwargs: The credential used to authenticate the user.
        """


UserSourceTypeSubClass = TypeVar("UserSourceTypeSubClass", bound=UserSourceType)


class UserSourceTypeRegistry(
    ModelRegistryMixin[UserSourceSubClass, UserSourceTypeSubClass],
    Registry[UserSourceTypeSubClass],
    CustomFieldsRegistryMixin,
):
    """
    Contains all the user_source types.
    """

    name = "user_source"


user_source_type_registry: UserSourceTypeRegistry = UserSourceTypeRegistry()
