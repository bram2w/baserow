from typing import Any, Dict, Union

from django.contrib.auth.models import AbstractUser

from rest_framework import serializers

from baserow.contrib.builder.api.workflow_actions.serializers import (
    PolymorphicServiceRequestSerializer,
    PolymorphicServiceSerializer,
)
from baserow.contrib.builder.elements.element_types import NavigationElementManager
from baserow.contrib.builder.formula_importer import import_formula
from baserow.contrib.builder.workflow_actions.models import (
    LocalBaserowCreateRowWorkflowAction,
    LocalBaserowUpdateRowWorkflowAction,
    LogoutWorkflowAction,
    NotificationWorkflowAction,
    OpenPageWorkflowAction,
    RefreshDataSourceWorkflowAction,
)
from baserow.contrib.builder.workflow_actions.registries import (
    BuilderWorkflowActionType,
)
from baserow.contrib.builder.workflow_actions.types import BuilderWorkflowActionDict
from baserow.core.formula.serializers import FormulaSerializerField
from baserow.core.formula.types import BaserowFormula
from baserow.core.integrations.models import Integration
from baserow.core.services.handler import ServiceHandler
from baserow.core.services.registries import service_type_registry
from baserow.core.workflow_actions.models import WorkflowAction


class NotificationWorkflowActionType(BuilderWorkflowActionType):
    type = "notification"
    model_class = NotificationWorkflowAction
    serializer_field_names = ["title", "description"]
    serializer_field_overrides = {
        "title": FormulaSerializerField(
            help_text="The title of the notification. Must be an formula.",
            required=False,
            allow_blank=True,
            default="",
        ),
        "description": FormulaSerializerField(
            help_text="The description of the notification. Must be an formula.",
            required=False,
            allow_blank=True,
            default="",
        ),
    }

    class SerializedDict(BuilderWorkflowActionDict):
        title: BaserowFormula
        description: BaserowFormula

    @property
    def allowed_fields(self):
        return super().allowed_fields + ["title", "description"]

    def get_pytest_params(self, pytest_data_fixture) -> Dict[str, Any]:
        return {"title": "'hello'", "description": "'there'"}

    def deserialize_property(self, prop_name, value, id_mapping: Dict) -> Any:
        """
        Migrate the formulas.
        """

        if prop_name == "title":
            return import_formula(value, id_mapping)

        if prop_name == "description":
            return import_formula(value, id_mapping)

        return super().deserialize_property(prop_name, value, id_mapping)


class OpenPageWorkflowActionType(BuilderWorkflowActionType):
    type = "open_page"
    model_class = OpenPageWorkflowAction

    @property
    def serializer_field_names(self):
        return (
            super().serializer_field_names
            + NavigationElementManager.serializer_field_names
            + ["url"]  # TODO remove in the next release
        )

    @property
    def allowed_fields(self):
        return (
            super().allowed_fields + NavigationElementManager.allowed_fields + ["url"]
        )  # TODO remove in the next release

    @property
    def serializer_field_overrides(self):
        return (
            super().serializer_field_overrides
            | NavigationElementManager().get_serializer_field_overrides()
            | {
                "url": serializers.CharField(
                    help_text="The url of the page to open.",
                    required=False,
                    allow_blank=True,
                    default="",
                )
            }  # TODO remove in the next release
        )

    class SerializedDict(
        BuilderWorkflowActionDict,
        NavigationElementManager.SerializedDict,
    ):
        url: str  # TODO remove in the next release, replace with "..."

    def get_pytest_params(self, pytest_data_fixture):
        return NavigationElementManager().get_pytest_params(pytest_data_fixture)

    def deserialize_property(self, prop_name, value, id_mapping: Dict) -> Any:
        """
        Migrate the formulas.
        """

        if prop_name == "url":  # TODO remove in the next release
            return import_formula(value, id_mapping)

        return super().deserialize_property(
            prop_name,
            NavigationElementManager().deserialize_property(
                prop_name, value, id_mapping
            ),
            id_mapping,
        )


class LogoutWorkflowActionType(BuilderWorkflowActionType):
    type = "logout"
    model_class = LogoutWorkflowAction

    class SerializedDict(BuilderWorkflowActionDict):
        ...

    def get_pytest_params(self, pytest_data_fixture) -> Dict[str, Any]:
        return {}


class RefreshDataSourceWorkflowAction(BuilderWorkflowActionType):
    type = "refresh_data_source"
    model_class = RefreshDataSourceWorkflowAction
    serializer_field_names = ["data_source_id"]
    serializer_field_overrides = {
        "data_source_id": serializers.IntegerField(
            allow_null=True,
            default=None,
            required=False,
            help_text="The ID of the Data Source to be refreshed.",
        ),
    }

    class SerializedDict(BuilderWorkflowActionDict):
        data_source_id: int

    def get_pytest_params(self, pytest_data_fixture) -> Dict[str, Any]:
        return {}

    @property
    def allowed_fields(self):
        return super().allowed_fields + ["data_source_id"]

    def deserialize_property(self, prop_name, value, id_mapping: Dict) -> Any:
        data_sources = id_mapping.get("builder_data_sources", {})
        if prop_name == "data_source_id" and value in data_sources:
            return data_sources[value]

        return super().deserialize_property(prop_name, value, id_mapping)


class BuilderWorkflowServiceActionType(BuilderWorkflowActionType):
    serializer_field_names = ["service"]
    serializer_field_overrides = {
        "service": serializers.SerializerMethodField(
            help_text="The Service this workflow action is dispatched by.",
            source="service",
        ),
    }

    class SerializedDict(BuilderWorkflowActionDict):
        service: Dict

    @property
    def allowed_fields(self):
        return super().allowed_fields + ["service"]

    def get_pytest_params(self, pytest_data_fixture) -> Dict[str, int]:
        service = pytest_data_fixture.create_local_baserow_upsert_row_service()
        return {"service": service}

    def get_pytest_params_serialized(
        self, pytest_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        service_type = service_type_registry.get_by_model(pytest_params["service"])
        return {"service": service_type.export_serialized(pytest_params["service"])}

    def serialize_property(self, workflow_action: WorkflowAction, prop_name: str):
        """
        You can customize the behavior of the serialization of a property with this
        hook.
        """

        if prop_name == "service":
            service = workflow_action.service.specific
            return service.get_type().export_serialized(service)
        return super().serialize_property(workflow_action, prop_name)

    def deserialize_property(
        self, prop_name: str, value: Any, id_mapping: Dict[str, Any]
    ) -> Any:
        """
        If the workflow action has a relation to a service, this method will
        map the service's new `integration_id` and call `import_service` on
        the serialized service values.

        :param prop_name: the name of the property being transformed.
        :param value: the value of this property.
        :param id_mapping: the id mapping dict.
        :return: the deserialized version for this property.
        """

        if prop_name == "service" and value:
            integration = None
            serialized_service = value
            integration_id = serialized_service.get("integration_id", None)
            if integration_id:
                integration_id = id_mapping["integrations"].get(
                    integration_id, integration_id
                )
                integration = Integration.objects.get(id=integration_id)

            return ServiceHandler().import_service(
                integration,
                serialized_service,
                id_mapping,
                import_formula=import_formula,
            )
        return super().deserialize_property(prop_name, value, id_mapping)


class UpsertRowWorkflowActionType(BuilderWorkflowServiceActionType):
    type = "upsert_row"
    request_serializer_field_overrides = {
        "service": PolymorphicServiceRequestSerializer(
            default=None,
            required=False,
            help_text="The service which this workflow action is associated with.",
        )
    }
    serializer_field_overrides = {
        "service": PolymorphicServiceSerializer(
            help_text="The service which this workflow action is associated with."
        )
    }
    request_serializer_field_names = ["service"]

    @property
    def allowed_fields(self):
        return super().allowed_fields + ["service"]

    def prepare_values(
        self,
        values: Dict[str, Any],
        user: AbstractUser,
        instance: Union[
            LocalBaserowCreateRowWorkflowAction, LocalBaserowUpdateRowWorkflowAction
        ] = None,
    ):
        """
        Responsible for preparing the upsert row workflow action. By default, the
        only step is to pass any `service` data into the upsert row service.

        :param values: The full workflow action values to prepare.
        :param user: The user on whose behalf the change is made.
        :param instance: A create or update row workflow action instance.
        :return: The modified workflow action values, prepared.
        """

        service_type = service_type_registry.get("local_baserow_upsert_row")

        if not instance:
            # If we haven't received a workflow action instance, we're preparing
            # as part of creating a new action. If this happens, we need to create
            # a new upsert row service.
            service = ServiceHandler().create_service(service_type)
        else:
            service = instance.service.specific

        # If we received any service values, prepare them.
        service_values = values.pop("service", None) or {}
        prepared_service_values = service_type.prepare_values(
            service_values, user, service
        )

        # Update the service instance with any prepared service values.
        ServiceHandler().update_service(
            service_type, service, **prepared_service_values
        )

        values["service"] = service
        return super().prepare_values(values, user, instance)


class CreateRowWorkflowActionType(UpsertRowWorkflowActionType):
    type = "create_row"
    model_class = LocalBaserowCreateRowWorkflowAction


class UpdateRowWorkflowActionType(UpsertRowWorkflowActionType):
    type = "update_row"
    model_class = LocalBaserowUpdateRowWorkflowAction
