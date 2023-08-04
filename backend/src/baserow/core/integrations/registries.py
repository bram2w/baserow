from abc import ABC
from typing import Any, Dict, Optional, Type, TypeVar

from django.contrib.auth.models import AbstractUser

from baserow.core.models import Application
from baserow.core.registry import (
    CustomFieldsInstanceMixin,
    CustomFieldsRegistryMixin,
    ImportExportMixin,
    Instance,
    ModelInstanceMixin,
    ModelRegistryMixin,
    Registry,
)

from .models import Integration
from .types import IntegrationDictSubClass, IntegrationSubClass


class IntegrationType(
    ModelInstanceMixin[Integration],
    ImportExportMixin[IntegrationSubClass],
    CustomFieldsInstanceMixin,
    Instance,
    ABC,
):
    SerializedDict: Type[IntegrationDictSubClass]

    """
    An integration type define a specific integration with a given external service.
    """

    def enhance_queryset(self, queryset):
        """
        Allow to enhance the queryset when querying the integration mainly to improve
        performances.
        """

        return queryset

    def prepare_values(
        self, values: Dict[str, Any], user: AbstractUser
    ) -> Dict[str, Any]:
        """
        The prepare_values hook gives the possibility to change the provided values
        that just before they are going to be used to create or update the instance. For
        example if an ID is provided, it can be converted to a model instance. Or to
        convert a certain date string to a date object. It's also an opportunity to add
        specific validations.

        :param values: The provided values.
        :param user: The user on whose behalf the change is made.
        :return: The updated values.
        """

        return values

    def get_property_for_serialization(self, integration: Integration, prop_name: str):
        if prop_name == "type":
            return self.type

        if prop_name == "order":
            return str(integration.order)

        return getattr(integration, prop_name)

    def export_serialized(
        self,
        integration: Integration,
    ) -> IntegrationDictSubClass:
        """Exports an integration in a format compatible with import serialized."""

        property_names = self.SerializedDict.__annotations__.keys()

        serialized = self.SerializedDict(
            **{
                key: self.get_property_for_serialization(integration, key)
                for key in property_names
            }
        )

        return serialized

    def import_serialized(
        self,
        application: Application,
        serialized_values: Dict[str, Any],
        id_mapping: Dict,
        cache: Optional[Dict] = None,
    ) -> IntegrationSubClass:
        """Imports a previously exported instance."""

        if "integrations" not in id_mapping:
            id_mapping["integrations"] = {}

        serialized_copy = serialized_values.copy()

        # Remove extra keys
        original_integration_id = serialized_copy.pop("id")
        serialized_copy.pop("type")

        integration = self.model_class(application=application, **serialized_copy)
        integration.save()

        id_mapping["integrations"][original_integration_id] = integration

        return integration


IntegrationTypeSubClass = TypeVar("IntegrationTypeSubClass", bound=IntegrationType)


class IntegrationTypeRegistry(
    ModelRegistryMixin[IntegrationSubClass, IntegrationTypeSubClass],
    Registry[IntegrationTypeSubClass],
    CustomFieldsRegistryMixin,
):
    """
    Contains all the integration types.
    """

    name = "integration"


integration_type_registry: IntegrationTypeRegistry = IntegrationTypeRegistry()
