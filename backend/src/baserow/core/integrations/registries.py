from abc import ABC
from typing import Any, Dict, List, Optional, Type, TypeVar

from django.contrib.auth.models import AbstractUser

from rest_framework import serializers

from baserow.api.integrations.fields import HasSecretField
from baserow.core.registry import (
    CustomFieldsInstanceMixin,
    CustomFieldsRegistryMixin,
    EasyImportExportMixin,
    Instance,
    ModelInstanceMixin,
    ModelRegistryMixin,
    Registry,
)

from .models import Integration
from .types import IntegrationDictSubClass, IntegrationSubClass


class IntegrationType(
    ModelInstanceMixin[Integration],
    EasyImportExportMixin[IntegrationSubClass],
    CustomFieldsInstanceMixin,
    Instance,
    ABC,
):
    SerializedDict: Type[IntegrationDictSubClass]
    parent_property_name = "application"
    id_mapping_name = "integrations"

    """
    An integration type define a specific integration with a given external service.
    """

    secret_fields: List[str] = []
    """
    Credentials that are write-only: they can be set and overwritten, but are
    never serialized back to any user, the creator included.

    This is deliberately narrower than `sensitive_fields`, which only governs
    what is stripped from a workspace export and which, for some types, covers
    ordinary configuration such as the host and port.
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

    def get_field_names(
        self, request_serializer: bool, extra_params=None, **kwargs
    ) -> List[str]:
        """
        Removes the secret fields from the response serializer and replaces each
        with a `has_<name>` boolean. The request serializer keeps them, because
        setting a credential is the only thing a user may do with it.
        """

        field_names = super().get_field_names(
            request_serializer, extra_params, **kwargs
        )

        if request_serializer or not self.secret_fields:
            return field_names

        return [name for name in field_names if name not in self.secret_fields] + [
            f"has_{name}" for name in self.secret_fields
        ]

    def get_field_overrides(
        self, request_serializer: bool, extra_params=None, **kwargs
    ) -> Dict:
        """
        Declares the `has_<name>` booleans on the response serializer, and makes
        every secret optional and blankable on the request serializer.

        The request side is not cosmetic. `IntegrationView.patch` validates
        without `partial=True`, so a model field that is neither `blank` nor
        `null` is generated as required. `SlackBotIntegration.token` is such a
        field, and once the token stops being returned the frontend no longer
        echoes it back, so without this override an unrelated rename would fail
        validation and clearing a token would be impossible.
        """

        overrides = super().get_field_overrides(
            request_serializer, extra_params, **kwargs
        )

        if not self.secret_fields:
            return overrides

        overrides = {**overrides}

        if request_serializer:
            for name in self.secret_fields:
                model_field = self.model_class._meta.get_field(name)
                overrides[name] = serializers.CharField(
                    required=False,
                    allow_blank=True,
                    allow_null=model_field.null,
                    max_length=model_field.max_length,
                    help_text=model_field.help_text,
                )
        else:
            for name in self.secret_fields:
                overrides[f"has_{name}"] = HasSecretField(name)

        return overrides

    def serialize_property(
        self,
        integration: Integration,
        prop_name: str,
        files_zip=None,
        storage=None,
        cache=None,
    ):
        if prop_name == "order":
            return str(integration.order)

        return super().serialize_property(
            integration, prop_name, files_zip=files_zip, storage=storage, cache=cache
        )

    def import_serialized(
        self,
        parent: Any,
        serialized_values: Dict[str, Any],
        id_mapping: Dict[str, Any],
        files_zip=None,
        storage=None,
        cache=None,
    ) -> IntegrationSubClass:
        return super().import_serialized(
            parent,
            serialized_values,
            id_mapping,
            files_zip=files_zip,
            storage=storage,
            cache=cache,
        )

    def after_import(self, user: AbstractUser, instance: Integration) -> None:
        """
        Hook to trigger any post import logic.
        """

    def get_context_data(self, instance: Integration) -> Optional[Dict]:
        """
        Get all the context data for an integration that is required by the editor to
        configure a service.

        :return: Context data
        """

        return None


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
