from abc import ABC
from typing import Any, Dict, Optional, Type, TypeVar

from django.contrib.auth.models import AbstractUser

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

    def serialize_property(self, user_source: UserSource, prop_name: str):
        if prop_name == "order":
            return str(user_source.order)

        return super().serialize_property(user_source, prop_name)

    def deserialize_property(
        self,
        prop_name: str,
        value: Any,
        id_mapping: Dict[str, Dict[int, int]],
        **kwargs
    ) -> Any:
        if prop_name == "integration_id":
            return id_mapping["integrations"][value]

        return super().deserialize_property(prop_name, value, id_mapping, **kwargs)

    def import_serialized(
        self,
        parent: Any,
        serialized_values: Dict[str, Any],
        id_mapping: Dict[str, Any],
        cache=None,
    ) -> UserSourceSubClass:
        return super().import_serialized(parent, serialized_values, id_mapping)


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
