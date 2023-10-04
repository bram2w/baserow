from typing import Any, Dict, Optional, Union

from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError

from rest_framework import serializers
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.fields import (
    BooleanField,
    CharField,
    ChoiceField,
    DateField,
    DateTimeField,
    DecimalField,
    Field,
    FloatField,
    IntegerField,
    TimeField,
    UUIDField,
)
from rest_framework.serializers import ListSerializer, Serializer

from baserow.contrib.database.api.fields.serializers import FieldSerializer
from baserow.contrib.database.api.rows.serializers import (
    RowSerializer,
    get_row_serializer_class,
)
from baserow.contrib.database.fields.handler import FieldHandler
from baserow.contrib.database.fields.registries import field_type_registry
from baserow.contrib.database.rows.operations import ReadDatabaseRowOperationType
from baserow.contrib.database.search.handler import SearchHandler
from baserow.contrib.database.table.handler import TableHandler
from baserow.contrib.database.table.operations import ListRowsDatabaseTableOperationType
from baserow.contrib.database.views.handler import ViewHandler
from baserow.contrib.integrations.local_baserow.integration_types import (
    LocalBaserowIntegrationType,
)
from baserow.contrib.integrations.local_baserow.mixins import (
    LocalBaserowTableServiceFilterableMixin,
    LocalBaserowTableServiceSearchableMixin,
    LocalBaserowTableServiceSortableMixin,
)
from baserow.contrib.integrations.local_baserow.models import (
    LocalBaserowGetRow,
    LocalBaserowListRows,
)
from baserow.core.formula import resolve_formula
from baserow.core.formula.registries import formula_runtime_function_registry
from baserow.core.formula.runtime_formula_context import RuntimeFormulaContext
from baserow.core.formula.serializers import FormulaSerializerField
from baserow.core.formula.validator import ensure_integer
from baserow.core.handler import CoreHandler
from baserow.core.services.exceptions import DoesNotExist, ServiceImproperlyConfigured
from baserow.core.services.registries import ServiceType
from baserow.core.services.types import ServiceDict, ServiceSubClass

LocalBaserowTableServiceSubClass = Union[LocalBaserowGetRow, LocalBaserowListRows]


class LocalBaserowServiceType(ServiceType):
    """
    The `ServiceType` for all `LocalBaserow` integration services.
    """

    def get_schema_for_return_type(
        self, service: ServiceSubClass, properties: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Responsible for returning the JSON Schema object based on the
        `returns_list` attribute set on this service type.

        :param service: The service we are generating a schema for.
        :param properties: A dictionary of properties which describe this service.
        :return: A JSON Schema formatted dictionary.
        """

        if self.returns_list:
            return {
                "items": {"type": "object", "properties": properties},
                "title": self.get_schema_name(service),
                "type": "array",
            }
        else:
            return {
                "properties": properties,
                "title": self.get_schema_name(service),
                "type": "object",
            }

    def guess_json_type_from_response_serialize_field(
        self, serializer_field: Union[Field, Serializer]
    ) -> Dict[str, Any]:
        """
        Responsible for taking a serializer field, and guessing what its JSON
        type will be. If the field is a ListSerializer, and it has a child serializer,
        we add the child's type as well.

        :param serializer_field: The serializer field.
        :return: A dictionary to add to our schema.
        """

        if isinstance(
            serializer_field, (UUIDField, CharField, DecimalField, FloatField)
        ):
            # DecimalField/FloatField values are returned as strings from the API.
            base_type = "string"
        elif isinstance(serializer_field, (DateTimeField, DateField, TimeField)):
            base_type = "string"
        elif isinstance(serializer_field, ChoiceField):
            base_type = "string"
        elif isinstance(serializer_field, IntegerField):
            base_type = "number"
        elif isinstance(serializer_field, BooleanField):
            base_type = "boolean"
        elif isinstance(serializer_field, ListSerializer):
            # ListSerializer.child is required, so add its subtype.
            sub_type = self.guess_json_type_from_response_serialize_field(
                serializer_field.child
            )
            return {"type": "array", "items": sub_type}
        elif issubclass(serializer_field.__class__, Serializer):
            properties = {}
            for name, child_serializer in serializer_field.get_fields().items():
                properties[name] = {
                    "title": name,
                    **self.guess_json_type_from_response_serialize_field(
                        child_serializer
                    ),
                }

            return {"type": "object", "properties": properties}
        else:
            base_type = None

        return {"type": base_type}


class LocalBaserowTableServiceType(LocalBaserowServiceType):
    """
    The `ServiceType` for `LocalBaserowTableService` subclasses.
    """

    def prepare_values(
        self,
        values: Dict[str, Any],
        user: AbstractUser,
        instance: Optional[ServiceSubClass] = None,
    ) -> Dict[str, Any]:
        """Load the table & view instance instead of the ID."""

        if "table_id" in values:
            table_id = values.pop("table_id")
            if table_id is not None:
                table = TableHandler().get_table(table_id)
                values["table"] = table

                # Reset the view if the table has changed
                if (
                    "view_id" not in values
                    and instance
                    and instance.view_id
                    and instance.view.table_id != table_id
                ):
                    values["view"] = None
            else:
                values["table"] = None

        if "view_id" in values:
            view_id = values.pop("view_id")
            if view_id is not None:
                view = ViewHandler().get_view(view_id)

                # Check that the view table_id match the given table
                if "table" in values and view.table_id != values["table"].id:
                    raise DRFValidationError(
                        detail=f"The view with ID {view_id} is not related to the "
                        "given table.",
                        code="invalid_view",
                    )

                # Check that the view table_id match the existing table
                elif (
                    instance
                    and instance.table_id
                    and view.table_id != instance.table_id
                ):
                    raise DRFValidationError(
                        detail=f"The view with ID {view_id} is not related to the "
                        "given table.",
                        code="invalid_view",
                    )
                else:
                    # Add the missing table
                    values["table"] = view.table
                values["view"] = view
            else:
                values["view"] = None

        return super().prepare_values(values, user)

    def generate_schema(
        self, service: LocalBaserowTableServiceSubClass
    ) -> Optional[Dict[str, Any]]:
        """
        Responsible for generating a dictionary in the JSON Schema spec. This helps
        inform the frontend data source form and data explorer about the type of
        schema the service is interacting with.

        :param service: A `LocalBaserowTableService` subclass.
        :return: A schema dictionary, or None if no `Table` has been applied.
        """

        table = service.table
        if not table:
            return None

        properties = {"id": {"type": "number", "title": "ID"}}
        fields = FieldHandler().get_fields(table, specific=True)
        for field in fields:
            field_type = field_type_registry.get_by_model(field)
            # Only `TextField` has a default value at the moment.
            default_value = getattr(field, "text_default", None)
            field_serializer = field_type.get_serializer(field, FieldSerializer)
            properties[field.db_column] = {
                "title": field.name,
                "default": default_value,
                "original_type": field_type.type,
                "metadata": field_serializer.data,
            } | self.get_json_type_from_response_serializer_field(field, field_type)

        return self.get_schema_for_return_type(service, properties)

    def get_schema_name(self, service: LocalBaserowTableServiceSubClass) -> str:
        """
        The default `LocalBaserowTableService` schema name.

        :param service: The service we want to generate a schema `title` with.
        :return: A string.
        """

        return f"Table{service.table_id}Schema"

    def get_json_type_from_response_serializer_field(
        self, field, field_type
    ) -> Dict[str, Any]:
        """
        Responsible for taking a `Field` and `FieldType`, getting the field type's
        response serializer field, and passing it into our serializer to JSON type
        mapping method, `guess_json_type_from_response_serialize_field`.

        :param field: The Baserow Field we want a type for.
        :param field_type: The Baserow FieldType we want a type for.
        :return: A dictionary to add to our schema.
        """

        serializer_field = field_type.get_response_serializer_field(field)
        return self.guess_json_type_from_response_serialize_field(serializer_field)


class LocalBaserowListRowsUserServiceType(
    LocalBaserowTableServiceType,
    LocalBaserowTableServiceFilterableMixin,
    LocalBaserowTableServiceSortableMixin,
    LocalBaserowTableServiceSearchableMixin,
):
    """
    This service gives access to a list of rows from the same Baserow instance as the
    one hosting the application.
    """

    integration_type = LocalBaserowIntegrationType.type
    type = "local_baserow_list_rows"
    model_class = LocalBaserowListRows
    max_result_limit = 200
    returns_list = True

    class SerializedDict(ServiceDict):
        table_id: int
        view_id: int
        search_query: str

    allowed_fields = ["table", "view", "search_query"]

    serializer_field_names = [
        "table_id",
        "view_id",
        "search_query",
    ]

    request_serializer_field_overrides = {
        "table_id": serializers.IntegerField(
            required=False,
            allow_null=True,
            help_text="The id of the Baserow table we want the data for.",
        ),
        "view_id": serializers.IntegerField(
            required=False,
            allow_null=True,
            help_text="The id of the Baserow view we want the data for.",
        ),
        "search_query": serializers.CharField(
            required=False,
            allow_blank=True,
            help_text="Any search terms to apply to the service when it is dispatched.",
        ),
    }

    def enhance_queryset(self, queryset):
        return queryset.select_related("view", "table").prefetch_related(
            "view__viewfilter_set",
            "view__viewsort_set",
            "table__field_set",
            "view__viewgroupby_set",
        )

    def transform_serialized_value(
        self, prop_name: str, value: Any, id_mapping: Dict[str, Any]
    ):
        """
        Get the view & table ID from the mapping if it exists.
        """

        if prop_name == "table_id" and "database_tables" in id_mapping:
            return id_mapping["database_tables"].get(value, None)

        if prop_name == "view_id" and "database_views" in id_mapping:
            return id_mapping["database_views"].get(value, None)

        return value

    def dispatch_data(
        self,
        service: LocalBaserowListRows,
        runtime_formula_context: Optional[RuntimeFormulaContext] = None,
    ) -> Dict[str, Any]:
        """
        Returns a list of rows from the table stored in the service instance.

        :param service: the local baserow get row service.
        :param runtime_formula_context: the context used for formula resolution.
        :raise ServiceImproperlyConfigured: if the table property is missing.
        :return: The list of rows.
        """

        integration = service.integration.specific

        table = service.table
        if table is None:
            raise ServiceImproperlyConfigured("The table property is missing.")

        CoreHandler().check_permissions(
            integration.authorized_user,
            ListRowsDatabaseTableOperationType.type,
            workspace=table.database.workspace,
            context=table,
        )

        model = table.get_model()
        queryset = model.objects.all().enhance_by_fields()

        # Apply the search query to this Service's View.
        search_query = self.get_dispatch_search(service)
        if search_query:
            search_mode = SearchHandler.get_default_search_mode_for_table(table)
            queryset = queryset.search_all_fields(search_query, search_mode=search_mode)

        # Find filters applicable to this service.
        queryset = self.get_dispatch_filters(service, queryset, model)

        # Find sorts applicable to this service.
        view_sorts, queryset = self.get_dispatch_sorts(service, queryset, model)
        if view_sorts is not None:
            queryset = queryset.order_by(*view_sorts)

        rows = queryset[: self.default_result_limit]

        return {"data": rows, "baserow_table_model": model}

    def dispatch_transform(
        self,
        dispatch_data: Dict[str, Any],
        **kwargs,
    ) -> Any:
        """
        Given the rows found in `dispatch_data`, serializes them.

        :param dispatch_data: The data generated by `dispatch_data`.
        :raise ServiceImproperlyConfigured: if the table property is missing.
        :return: The list of rows.
        """

        serializer = get_row_serializer_class(
            dispatch_data["baserow_table_model"],
            RowSerializer,
            is_response=True,
        )
        return serializer(dispatch_data["data"], many=True).data


class LocalBaserowGetRowUserServiceType(
    LocalBaserowTableServiceType,
    LocalBaserowTableServiceFilterableMixin,
    LocalBaserowTableServiceSearchableMixin,
):
    """
    This service gives access to one specific row from a given table from the same
    Baserow instance as the one hosting the application.
    """

    integration_type = LocalBaserowIntegrationType.type
    type = "local_baserow_get_row"
    model_class = LocalBaserowGetRow

    class SerializedDict(ServiceDict):
        table_id: int
        view_id: int
        row_id: str
        search_query: str

    allowed_fields = ["table", "view", "row_id", "search_query"]

    serializer_field_names = [
        "table_id",
        "view_id",
        "row_id",
        "search_query",
    ]

    request_serializer_field_overrides = {
        "table_id": serializers.IntegerField(
            required=False,
            allow_null=True,
            help_text="The id of the Baserow table we want the data for.",
        ),
        "view_id": serializers.IntegerField(
            required=False,
            allow_null=True,
            help_text="The id of the Baserow view we want the data for.",
        ),
        "row_id": FormulaSerializerField(
            required=False,
            allow_blank=True,
            help_text="A formula for defining the intended row.",
        ),
        "search_query": serializers.CharField(
            required=False,
            allow_blank=True,
            help_text="Any search queries to apply to the "
            "service when it is dispatched.",
        ),
    }

    def enhance_queryset(self, queryset):
        return queryset.select_related(
            "table", "table__database", "table__database__workspace", "view"
        )

    def transform_serialized_value(
        self, prop_name: str, value: Any, id_mapping: Dict[str, Any]
    ):
        """
        Get the view & table ID from the mapping if it exists.
        """

        if prop_name == "table_id" and "database_tables" in id_mapping:
            return id_mapping["database_tables"].get(value, None)

        if prop_name == "view_id" and "database_tables" in id_mapping:
            return id_mapping["database_tables"].get(value, None)

        return value

    def dispatch_transform(
        self,
        dispatch_data: Dict[str, Any],
    ) -> Any:
        """
        Responsible for serializing the `dispatch_data` row.

        :param dispatch_data: The `dispatch_data` result.
        :return:
        """

        serializer = get_row_serializer_class(
            dispatch_data["baserow_table_model"], RowSerializer, is_response=True
        )
        serialized_row = serializer(dispatch_data["data"]).data

        return serialized_row

    def dispatch_data(
        self,
        service: LocalBaserowGetRow,
        runtime_formula_context: RuntimeFormulaContext,
    ) -> Dict[str, Any]:
        """
        Returns the row targeted by the `row_id` formula from the table stored in the
        service instance.

        :param service: the local baserow get row service.
        :param runtime_formula_context: the context used for formula resolution.
        :raise ServiceImproperlyConfigured: if the table property is missing or if the
            formula can't be resolved.
        :raise DoesNotExist: if row id doesn't exist.
        :return: The rows.
        """

        integration = service.integration.specific

        table = service.table
        if table is None:
            raise ServiceImproperlyConfigured("The table property is missing.")

        try:
            row_id = ensure_integer(
                resolve_formula(
                    service.row_id,
                    formula_runtime_function_registry,
                    runtime_formula_context,
                )
            )
        except ValidationError:
            raise ServiceImproperlyConfigured(
                "The result of the `row_id` formula must be an integer or convertible "
                "to an integer."
            )
        except Exception as e:
            raise ServiceImproperlyConfigured(
                f"The `row_id` formula can't be resolved: {e}"
            )

        CoreHandler().check_permissions(
            integration.authorized_user,
            ReadDatabaseRowOperationType.type,
            workspace=table.database.workspace,
            context=table,
        )

        model = table.get_model()
        queryset = model.objects.all()

        # Apply the search query to this Service's View.
        search_query = self.get_dispatch_search(service)
        if search_query:
            search_mode = SearchHandler.get_default_search_mode_for_table(table)
            queryset = queryset.search_all_fields(search_query, search_mode=search_mode)

        # Find the `filters` applicable to this Service's View.
        queryset = self.get_dispatch_filters(service, queryset, model)

        try:
            row = queryset.get(pk=row_id)
            return {"data": row, "baserow_table_model": model}
        except model.DoesNotExist:
            raise DoesNotExist()
