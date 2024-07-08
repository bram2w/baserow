from abc import ABC
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, TypeVar
from zipfile import ZipFile

from django.contrib.auth.models import AbstractUser
from django.core.files.storage import Storage

from rest_framework.exceptions import ValidationError as DRFValidationError

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
from baserow.core.services.dispatch_context import DispatchContext

from ..integrations.exceptions import IntegrationDoesNotExist
from .models import Service
from .types import ServiceDictSubClass, ServiceSubClass


class DispatchTypes(str, Enum):
    # A `ServiceType` which is used by a `WorkflowAction`.
    DISPATCH_WORKFLOW_ACTION = "dispatch-action"
    # A `ServiceType` which is used by a `DataSource`.
    DISPATCH_DATA_SOURCE = "dispatch-data-source"


class ServiceType(
    ModelInstanceMixin[Service],
    EasyImportExportMixin[ServiceSubClass],
    CustomFieldsInstanceMixin,
    Instance,
    ABC,
):
    """
    A service type describe a specific service of an external integration.
    """

    integration_type = None

    SerializedDict: Type[ServiceDictSubClass]
    parent_property_name = "integration"
    id_mapping_name = "services"

    # The maximum number of records this service is able to return.
    # By default, the maximum is `None`, which is unlimited.
    max_result_limit = None

    # The default number of records this service will return,
    # unless instructed otherwise by a user.
    default_result_limit = max_result_limit

    # Does this service return a list of record?
    returns_list = False

    # What parent object is responsible for dispatching this `ServiceType`?
    # It could be via a `DataSource`, in which case `DISPATCH_DATA_SOURCE`
    # should be chosen, or via a `WorkflowAction`, in which case
    # `DISPATCH_WORKFLOW_ACTION` should be chosen.
    dispatch_type = None

    def prepare_values(
        self,
        values: Dict[str, Any],
        user: AbstractUser,
        instance: Optional[ServiceSubClass] = None,
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
                try:
                    integration = IntegrationHandler().get_integration(integration_id)
                except IntegrationDoesNotExist:
                    raise DRFValidationError(
                        f"The integration with ID {integration_id} does not exist."
                    )
                values["integration"] = integration
            else:
                values["integration"] = None

        return values

    def after_create(self, instance: ServiceSubClass, values: Dict):
        """
        This hook is called right after the service has been created.

        :param instance: The created service instance.
        :param values: The values that were passed when creating the service
            metadata.
        """

    def after_update(
        self,
        instance: ServiceSubClass,
        values: Dict,
        changes: Dict[str, Tuple],
    ):
        """
        This hook is called right after the service has been updated.

        :param instance: The updated service instance.
        :param values: The values that were passed when creating the service
            metadata.
        :param changes: A dictionary containing all changes which were made to the
            service prior to `after_update` being called.
        """

    def before_delete(self, instance: ServiceSubClass):
        """
        This hook is called just before the service will be deleted.

        :param instance: The to be deleted service instance.
        """

    def get_context_data(self, service: ServiceSubClass):
        """
        Return the context data for this service.

        This can be overridden by child classes to provide extra context data,
        to complement this service results.
        """

        return None

    def get_context_data_schema(self, service: ServiceSubClass):
        """Return the schema for the context data."""

        return None

    def resolve_service_formulas(
        self,
        service: ServiceSubClass,
        dispatch_context: DispatchContext,
    ) -> Dict[str, Any]:
        """
        Responsible for resolving any formulas in the service's fields, and then
        performing a validation step prior to `ServiceType.dispatch_data` is executed.

        :param service: The service instance we want to use.
        :param dispatch_context: The runtime_formula_context instance used to
            resolve formulas (if any).
        :return: Any
        """

        return {}

    def dispatch_transform(
        self,
        data: Any,
    ) -> Any:
        """
        Responsible for taking the `dispatch_data` result and transforming its value
        for API consumer's consumption.

        :param data: The `dispatch_data` result.
        :return: The transformed `dispatch_transform` result if any.
        """

    def dispatch_data(
        self,
        service: ServiceSubClass,
        resolved_values: Dict[str, Any],
        dispatch_context: DispatchContext,
    ) -> Any:
        """
        Responsible for executing the service's principle task.

        :param service: The service instance to dispatch with.
        :param resolved_values: If the service has any formulas, this dictionary will
            contain their resolved values.
        :param dispatch_context: The context used for the dispatch.
        :return: The service `dispatch_data` result if any.
        """

    def dispatch(
        self,
        service: ServiceSubClass,
        dispatch_context: DispatchContext,
    ) -> Any:
        """
        Responsible for calling `dispatch_data` and `dispatch_transform` to execute
        the service's task, and generating the dispatch's response, respectively.

        :param service: The service instance to dispatch with.
        :param dispatch_context: The context used for the dispatch.
        :return: The service dispatch result if any.
        """

        resolved_values = self.resolve_service_formulas(service, dispatch_context)
        data = self.dispatch_data(service, resolved_values, dispatch_context)
        return self.dispatch_transform(data)

    def get_schema_name(self, service: Service) -> str:
        """
        The default schema name added to the `title` in a JSON Schema object.

        :param service: The service we want to generate a schema `title` with.
        :return: A string.
        """

        return f"Service{service.id}Schema"

    def generate_schema(self, service: Service) -> Optional[Dict[str, Any]]:
        """
        Responsible for generating the full JSON Schema response. Must be
        overridden by child classes so that the can return their service's
        schema.

        :param service: The service we want to generate a schema for.
        :return: None, or a dictionary representing the schema.
        """

        return None

    def enhance_queryset(self, queryset):
        """
        Allow to enhance the queryset when querying the service mainly to improve
        performances.
        """

        return queryset

    def deserialize_property(
        self,
        prop_name: str,
        value: Any,
        id_mapping: Dict[str, Any],
        files_zip: Optional[ZipFile] = None,
        storage: Optional[Storage] = None,
        cache: Optional[Dict] = None,
        import_formula: Callable[[str, Dict[str, Any]], str] = None,
        **kwargs,
    ) -> Any:
        """
        This hooks allow to customize the deserialization of a property.

        :param prop_name: the name of the property being transformed.
        :param value: the value of this property.
        :param id_mapping: the id mapping dict.
        :param import_formula: the import formula function.
        :return: the deserialized version for this property.
        """

        if import_formula is None:
            raise ValueError("Missing import formula function.")

        return super().deserialize_property(
            prop_name,
            value,
            id_mapping,
            files_zip=files_zip,
            storage=storage,
            cache=cache,
            **kwargs,
        )

    def import_path(self, path, id_mapping, **kwargs):
        """
        Allows to hook into the path import resolution.

        If not implemented, returns the path as it is.
        """

        return path

    def import_context_path(
        self, path: List[str], id_mapping: Dict[int, int], **kwargs
    ):
        """
        Allows to hook into the context path import resolution.

        If not implemented, returns the path as it is.
        """

        return path


ServiceTypeSubClass = TypeVar("ServiceTypeSubClass", bound=ServiceType)


class ServiceTypeRegistry(
    ModelRegistryMixin[ServiceSubClass, ServiceTypeSubClass],
    Registry[ServiceTypeSubClass],
    CustomFieldsRegistryMixin,
):
    """
    Contains the registered service types.
    """

    name = "integration_service"


service_type_registry: ServiceTypeRegistry = ServiceTypeRegistry()
