from typing import Any, Callable, Dict, List, Optional, Tuple, Union

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

from baserow.contrib.builder.formula_importer import import_formula
from baserow.contrib.database.api.fields.serializers import (
    DurationFieldSerializer,
    FieldSerializer,
)
from baserow.contrib.database.api.rows.serializers import (
    RowSerializer,
    get_row_serializer_class,
)
from baserow.contrib.database.fields.exceptions import FieldDoesNotExist
from baserow.contrib.database.fields.handler import FieldHandler
from baserow.contrib.database.fields.registries import field_type_registry
from baserow.contrib.database.rows.handler import RowHandler
from baserow.contrib.database.rows.operations import ReadDatabaseRowOperationType
from baserow.contrib.database.search.handler import SearchHandler
from baserow.contrib.database.table.exceptions import TableDoesNotExist
from baserow.contrib.database.table.handler import TableHandler
from baserow.contrib.database.table.operations import ListRowsDatabaseTableOperationType
from baserow.contrib.database.table.service import TableService
from baserow.contrib.database.views.service import ViewService
from baserow.contrib.integrations.local_baserow.api.serializers import (
    LocalBaserowTableServiceFieldMappingSerializer,
    LocalBaserowTableServiceFilterSerializer,
    LocalBaserowTableServiceSortSerializer,
)
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
    LocalBaserowTableServiceFieldMapping,
    LocalBaserowTableServiceFilter,
    LocalBaserowTableServiceSort,
    LocalBaserowUpsertRow,
)
from baserow.core.formula import BaserowFormula, resolve_formula
from baserow.core.formula.registries import formula_runtime_function_registry
from baserow.core.formula.serializers import FormulaSerializerField
from baserow.core.formula.validator import ensure_integer
from baserow.core.handler import CoreHandler
from baserow.core.services.dispatch_context import DispatchContext
from baserow.core.services.exceptions import DoesNotExist, ServiceImproperlyConfigured
from baserow.core.services.registries import DispatchTypes, ServiceType
from baserow.core.services.types import (
    ServiceDict,
    ServiceFilterDictSubClass,
    ServiceSortDictSubClass,
    ServiceSubClass,
)
from baserow.core.utils import atomic_if_not_already


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
        elif isinstance(
            serializer_field,
            (DateTimeField, DateField, TimeField, DurationFieldSerializer),
        ):
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

    def resolve_service_formulas(
        self,
        service: ServiceSubClass,
        dispatch_context: DispatchContext,
    ) -> Dict[str, Any]:
        """
        A hook called before the `LocalBaserowTableServiceType` subclass dispatch
        calls. It ensures we check the service has a `Table` before execution.

        :param service: A `LocalBaserowTableService` instance.
        :param dispatch_context: The dispatch_context instance used to
            resolve formulas (if any).
        :raises ServiceImproperlyConfigured: When we try and dispatch a service that
            has no `Table` associated with it, or if the table/database is trashed.
        """

        if service.table_id is None:
            raise ServiceImproperlyConfigured("The table property is missing.")

        try:
            table = TableHandler().get_table(service.table_id)
        except TableDoesNotExist as e:
            raise ServiceImproperlyConfigured("The specified table is trashed") from e

        resolved_values = super().resolve_service_formulas(service, dispatch_context)
        resolved_values["table"] = table

        return resolved_values

    def serialize_property(self, service: ServiceSubClass, prop_name: str):
        """
        Responsible for serializing the `filters` and `sortings` properties.

        :param service: The LocalBaserowListRows service.
        :param prop_name: The property name we're serializing.
        :return: Any
        """

        if prop_name == "filters":
            return [
                {
                    "field_id": f.field_id,
                    "type": f.type,
                    "value": f.value,
                    "value_is_formula": f.value_is_formula,
                }
                for f in service.service_filters.all()
            ]
        if prop_name == "sortings":
            return [
                {
                    "field_id": s.field_id,
                    "order_by": s.order_by,
                }
                for s in service.service_sorts.all()
            ]

        return super().serialize_property(service, prop_name)

    def deserialize_property(
        self, prop_name: str, value: Any, id_mapping: Dict[str, Any], **kwargs
    ):
        """
        Get the view, table and field IDs from the mapping if they exists.
        """

        if prop_name == "table_id" and "database_tables" in id_mapping:
            return id_mapping["database_tables"].get(value, None)

        if "database_fields" in id_mapping and prop_name in ["filters", "sortings"]:
            return [
                {
                    **item,
                    "field_id": id_mapping["database_fields"][item["field_id"]],
                }
                for item in value
            ]

        return super().deserialize_property(prop_name, value, id_mapping, **kwargs)

    def create_instance_from_serialized(self, serialized_values):
        """
        Responsible for creating the `filters` and `sortings`.

        :param page: The Page we're importing a data source for.
        :param serialized_values: The serialized values we'll use to import.
        :param id_mapping: The id_mapping dictionary.
        :return: A Service.
        """

        filters = serialized_values.pop("filters", [])
        sortings = serialized_values.pop("sortings", [])

        service = super().create_instance_from_serialized(serialized_values)

        # Create filters
        LocalBaserowTableServiceFilter.objects.bulk_create(
            [
                LocalBaserowTableServiceFilter(
                    **service_filter,
                    order=index,
                    service=service,
                )
                for index, service_filter in enumerate(filters)
            ]
        )

        # Create sortings
        LocalBaserowTableServiceSort.objects.bulk_create(
            [
                LocalBaserowTableServiceSort(
                    **service_sorting,
                    order=index,
                    service=service,
                )
                for index, service_sorting in enumerate(sortings)
            ]
        )

        return service

    def update_service_sortings(
        self,
        service: Union[LocalBaserowGetRow, LocalBaserowListRows],
        service_sorts: Optional[List[ServiceSortDictSubClass]] = None,
    ):
        with atomic_if_not_already():
            service.service_sorts.all().delete()
            LocalBaserowTableServiceSort.objects.bulk_create(
                [
                    LocalBaserowTableServiceSort(
                        **service_sort, service=service, order=index
                    )
                    for index, service_sort in enumerate(service_sorts)
                ]
            )

    def update_service_filters(
        self,
        service: Union[LocalBaserowGetRow, LocalBaserowListRows],
        service_filters: Optional[List[ServiceFilterDictSubClass]] = None,
    ):
        with atomic_if_not_already():
            service.service_filters.all().delete()
            LocalBaserowTableServiceFilter.objects.bulk_create(
                [
                    LocalBaserowTableServiceFilter(
                        **service_filter, service=service, order=index
                    )
                    for index, service_filter in enumerate(service_filters)
                ]
            )

    def after_update(
        self,
        instance: ServiceSubClass,
        values: Dict,
        changes: Dict[str, Tuple],
    ) -> None:
        """
        Responsible for updating service filters and sorts which have been
        PATCHED to the data source / service endpoint. At the moment we
        destroy all current filters and sorts, and create the ones present
        in `service_filters` / `service_sorts` respectively.

        :param instance: The service we want to manage filters/sorts for.
        :param values: A dictionary which may contain filters/sorts.
        :param changes: A dictionary containing all changes which were made to the
            service prior to `after_update` being called.
        """

        # Following a Table change, from one Table to another, we drop all filters
        # and sorts. This is due to the fact that both point at specific table fields.
        from_table, to_table = changes.get("table", (None, None))
        if from_table and to_table:
            instance.service_filters.all().delete()
            instance.service_sorts.all().delete()
        else:
            if "service_filters" in values:
                self.update_service_filters(instance, values["service_filters"])
            if "service_sorts" in values:
                self.update_service_sortings(instance, values["service_sorts"])

    def prepare_values(
        self,
        values: Dict[str, Any],
        user: AbstractUser,
        instance: Optional[ServiceSubClass] = None,
    ) -> Dict[str, Any]:
        """Load the table instance instead of the ID."""

        # Check if we already have a table. We may have already
        # added it in `LocalBaserowViewServiceType.prepare_values`.
        if "table_id" in values and "table" not in values:
            table_id = values.pop("table_id")
            if table_id is not None:
                try:
                    table = TableService().get_table(user, table_id)
                except TableDoesNotExist:
                    raise DRFValidationError(
                        f"The table with ID {table_id} does not exist."
                    )
                values["table"] = table
            else:
                values["table"] = None

        return super().prepare_values(values, user, instance)

    def generate_schema(self, service: ServiceSubClass) -> Optional[Dict[str, Any]]:
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

        properties = {"id": {"type": "number", "title": "Id"}}
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

    def get_schema_name(self, service: ServiceSubClass) -> str:
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


class LocalBaserowViewServiceType(LocalBaserowTableServiceType):
    """
    The `ServiceType` for `LocalBaserowViewService` subclasses.
    """

    def deserialize_property(
        self,
        prop_name: str,
        value: Any,
        id_mapping: Dict[str, Any],
        **kwargs,
    ):
        """
        Get the view ID from the mapping if it exists.
        """

        if prop_name == "view_id" and "database_views" in id_mapping:
            return id_mapping["database_views"].get(value, None)

        return super().deserialize_property(prop_name, value, id_mapping, **kwargs)

    def prepare_values(
        self,
        values: Dict[str, Any],
        user: AbstractUser,
        instance: Optional[ServiceSubClass] = None,
    ) -> Dict[str, Any]:
        """Load the table & view instance instead of the ID."""

        # Call the super first as it'll fetch the table for us.
        values = super().prepare_values(values, user, instance)

        if "table" in values:
            # Reset the view if the table has changed
            if (
                "view_id" not in values
                and instance
                and instance.view_id
                and instance.view.table_id != values["table"].id
            ):
                values["view"] = None

        if "view_id" in values:
            view_id = values.pop("view_id")
            if view_id is not None:
                view = ViewService().get_view(user, view_id)

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

        return super().prepare_values(values, user, instance)


class LocalBaserowListRowsUserServiceType(
    LocalBaserowViewServiceType,
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
    dispatch_type = DispatchTypes.DISPATCH_DATA_SOURCE

    allowed_fields = [
        "search_query",
        "table",
        "view",
        "filter_type",
    ]
    serializer_field_names = [
        "table_id",
        "view_id",
        "filter_type",
        "search_query",
        "sortings",
        "filters",
    ]
    serializer_field_overrides = {
        "filters": LocalBaserowTableServiceFilterSerializer(
            many=True, source="service_filters", required=False
        ),
        "sortings": LocalBaserowTableServiceSortSerializer(
            many=True, source="service_sorts", required=False
        ),
    }
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
        "search_query": FormulaSerializerField(
            required=False,
            allow_blank=True,
            help_text="Any search queries to apply to the "
            "service when it is dispatched.",
        ),
    } | serializer_field_overrides

    class SerializedDict(ServiceDict):
        table_id: int
        view_id: int
        search_query: str
        filters: List[Dict]
        sortings: List[Dict]

    def enhance_queryset(self, queryset):
        return queryset.select_related("view", "table").prefetch_related(
            "view__viewfilter_set",
            "view__filter_groups",
            "view__viewsort_set",
            "table__field_set",
            "view__viewgroupby_set",
        )

    def import_path(self, path, id_mapping):
        """
        Updates the field ids in the path.
        """

        row, field_dbname, *rest = path

        if field_dbname == "id":
            return path

        original_field_id = int(field_dbname[6:])
        field_id = id_mapping.get("database_fields", {}).get(
            original_field_id, original_field_id
        )

        return [row, f"field_{field_id}", *rest]

    def deserialize_property(
        self,
        prop_name: str,
        value: Any,
        id_mapping: Dict[str, Any],
        import_formula: Callable[[str, Dict[str, Any]], str] = lambda x, y: x,
        **kwargs,
    ):
        """
        Responsible for deserializing the `search_query` and `filters` property
        by importing its formula.

        :param prop_name: the name of the property being transformed.
        :param value: the value of this property.
        :param id_mapping: the id mapping dict.
        :param import_formula: the import formula function.
        :return: the deserialized version for this property.
        """

        if prop_name == "search_query":
            return import_formula(value, id_mapping)

        if prop_name == "filters":
            return [
                {
                    **f,
                    "value": (
                        import_formula(f["value"], id_mapping)
                        if f["value_is_formula"]
                        else f["value"]
                    ),
                    "field_id": (
                        id_mapping["database_fields"][f["field_id"]]
                        if "database_fields" in id_mapping
                        else f["field_id"]
                    ),
                }
                for f in value
            ]

        return super().deserialize_property(
            prop_name, value, id_mapping, import_formula=import_formula, **kwargs
        )

    def dispatch_data(
        self,
        service: LocalBaserowListRows,
        resolved_values: Dict[str, Any],
        dispatch_context: DispatchContext,
    ) -> Dict[str, Any]:
        """
        Returns a list of rows from the table stored in the service instance.

        :param service: the local baserow get row service.
        :param resolved_values: If the service has any formulas, this dictionary will
            contain their resolved values.
        :param dispatch_context: The context used for the dispatch.
        :return: The list of rows.
        """

        table = resolved_values["table"]

        integration = service.integration.specific

        CoreHandler().check_permissions(
            integration.authorized_user,
            ListRowsDatabaseTableOperationType.type,
            workspace=table.database.workspace,
            context=table,
        )

        model = table.get_model()
        queryset = model.objects.all().enhance_by_fields()

        # Apply the search query to this Service's View.
        search_query = self.get_dispatch_search(service, dispatch_context)
        if search_query:
            search_mode = SearchHandler.get_default_search_mode_for_table(table)
            queryset = queryset.search_all_fields(search_query, search_mode=search_mode)

        # Find filters applicable to this service.
        queryset = self.get_dispatch_filters(service, queryset, model, dispatch_context)

        # Find sorts applicable to this service.
        view_sorts, queryset = self.get_dispatch_sorts(service, queryset, model)
        if view_sorts is not None:
            queryset = queryset.order_by(*view_sorts)

        offset, count = dispatch_context.range(service)

        # We query one more row to be able to know if there is another page that can be
        # loaded.
        fake_count = min(self.max_result_limit, count) + 1

        rows = list(queryset[offset : offset + fake_count])

        has_next_page = len(rows) == fake_count

        return {
            "results": rows[:-1] if has_next_page else rows,
            "has_next_page": has_next_page,
            "baserow_table_model": model,
        }

    def dispatch_transform(
        self,
        dispatch_data: Dict[str, Any],
        **kwargs,
    ) -> Any:
        """
        Given the rows found in `dispatch_data`, serializes them.

        :param dispatch_data: The data generated by `dispatch_data`.
        :return: The list of rows.
        """

        serializer = get_row_serializer_class(
            dispatch_data["baserow_table_model"],
            RowSerializer,
            is_response=True,
        )

        return {
            "results": serializer(dispatch_data["results"], many=True).data,
            "has_next_page": dispatch_data["has_next_page"],
        }


class LocalBaserowGetRowUserServiceType(
    LocalBaserowViewServiceType,
    LocalBaserowTableServiceFilterableMixin,
    LocalBaserowTableServiceSortableMixin,
    LocalBaserowTableServiceSearchableMixin,
):
    """
    This service gives access to one specific row from a given table from the same
    Baserow instance as the one hosting the application.
    """

    integration_type = LocalBaserowIntegrationType.type
    type = "local_baserow_get_row"
    model_class = LocalBaserowGetRow
    dispatch_type = DispatchTypes.DISPATCH_DATA_SOURCE

    allowed_fields = [
        "row_id",
        "search_query",
        "table",
        "view",
        "filter_type",
    ]
    serializer_field_names = [
        "row_id",
        "table_id",
        "view_id",
        "filter_type",
        "search_query",
        "filters",
    ]
    serializer_field_overrides = {
        "filters": LocalBaserowTableServiceFilterSerializer(
            many=True, source="service_filters", required=False
        ),
    }
    request_serializer_field_overrides = {
        "row_id": FormulaSerializerField(
            required=False,
            allow_blank=True,
            help_text="A formula for defining the intended row.",
        ),
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
        "search_query": FormulaSerializerField(
            required=False,
            allow_blank=True,
            help_text="Any search queries to apply to the "
            "service when it is dispatched.",
        ),
    } | serializer_field_overrides

    class SerializedDict(ServiceDict):
        table_id: int
        view_id: int
        filters: List[Dict]
        row_id: BaserowFormula
        search_query: BaserowFormula

    def enhance_queryset(self, queryset):
        return queryset.select_related(
            "table", "table__database", "table__database__workspace", "view"
        )

    def import_path(self, path, id_mapping):
        """
        Updates the field ids in the path.
        """

        field_dbname, *rest = path

        if field_dbname == "id":
            return path

        original_field_id = int(field_dbname[6:])
        field_id = id_mapping.get("database_fields", {}).get(
            original_field_id, original_field_id
        )

        return [f"field_{field_id}", *rest]

    def deserialize_property(
        self,
        prop_name: str,
        value: Any,
        id_mapping: Dict[str, Any],
        import_formula: Callable[[str, Dict[str, Any]], str] = lambda x, y: x,
        **kwargs,
    ):
        """
        Get the view & table ID from the mapping if it exists and also updates the
        row_id, search_query & filters formulas.
        """

        if prop_name == "row_id":
            return import_formula(value, id_mapping)

        if prop_name == "filters":
            return [
                {
                    **f,
                    "value": (
                        import_formula(f["value"], id_mapping)
                        if f["value_is_formula"]
                        else f["value"]
                    ),
                    "field_id": (
                        id_mapping["database_fields"][f["field_id"]]
                        if "database_fields" in id_mapping
                        else f["field_id"]
                    ),
                }
                for f in value
            ]

        if prop_name == "search_query":
            return import_formula(value, id_mapping)

        return super().deserialize_property(
            prop_name, value, id_mapping, import_formula=import_formula, **kwargs
        )

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

    def resolve_service_formulas(
        self,
        service: ServiceSubClass,
        dispatch_context: DispatchContext,
    ) -> Dict[str, Any]:
        """
        :param service: A `LocalBaserowTableService` instance.
        :param dispatch_context: The dispatch_context instance used to
            resolve formulas (if any).
        :raises ServiceImproperlyConfigured: When we try and dispatch a service that
            has no `Table` associated with it.
        """

        resolved_values = super().resolve_service_formulas(service, dispatch_context)

        # Ignore validation for empty formulas
        if not service.row_id:
            return resolved_values

        try:
            resolved_values["row_id"] = ensure_integer(
                resolve_formula(
                    service.row_id,
                    formula_runtime_function_registry,
                    dispatch_context,
                )
            )
        except ValidationError as exc:
            raise ServiceImproperlyConfigured(
                "The result of the `row_id` formula must be an integer or convertible "
                "to an integer."
            ) from exc
        except Exception as exc:
            raise ServiceImproperlyConfigured(
                f"The `row_id` formula can't be resolved: {exc}"
            ) from exc

        return resolved_values

    def dispatch_data(
        self,
        service: LocalBaserowGetRow,
        resolved_values: Dict[str, Any],
        dispatch_context: DispatchContext,
    ) -> Dict[str, Any]:
        """
        Returns the row targeted by the `row_id` formula from the table stored in the
        service instance.

        :param service: the local baserow get row service.
        :param resolved_values: If the service has any formulas, this dictionary will
            contain their resolved values.
        :param dispatch_context: The context used for the dispatch.
        :return: The rows.
        """

        table = resolved_values["table"]
        integration = service.integration.specific

        CoreHandler().check_permissions(
            integration.authorized_user,
            ReadDatabaseRowOperationType.type,
            workspace=table.database.workspace,
            context=table,
        )

        model = table.get_model()
        queryset = model.objects.all()

        # Apply the search query to this Service's View.
        search_query = self.get_dispatch_search(service, dispatch_context)
        if search_query:
            search_mode = SearchHandler.get_default_search_mode_for_table(table)
            queryset = queryset.search_all_fields(search_query, search_mode=search_mode)

        # Find the `filters` applicable to this Service's View.
        queryset = self.get_dispatch_filters(service, queryset, model, dispatch_context)

        # Find sorts applicable to this service.
        view_sorts, queryset = self.get_dispatch_sorts(service, queryset, model)
        if view_sorts is not None:
            queryset = queryset.order_by(*view_sorts)

        # If no row id is provided return the first item from the queryset
        # This is useful when we want to use filters to specifically choose one
        # row by setting the right condition
        if "row_id" not in resolved_values:
            if not queryset.exists():
                raise DoesNotExist()
            return {"data": queryset.first(), "baserow_table_model": model}

        try:
            row = queryset.get(pk=resolved_values["row_id"])
            return {"data": row, "baserow_table_model": model}
        except model.DoesNotExist:
            raise DoesNotExist()


class LocalBaserowUpsertRowServiceType(LocalBaserowTableServiceType):
    """
    A `LocalBaserow` service type which will create or update rows in
    the service's target table when it is used in conjunction with
    workflow actions.
    """

    integration_type = LocalBaserowIntegrationType.type
    type = "local_baserow_upsert_row"
    model_class = LocalBaserowUpsertRow
    dispatch_type = DispatchTypes.DISPATCH_WORKFLOW_ACTION

    allowed_fields = ["table", "row_id", "integration"]
    serializer_field_names = ["table_id", "row_id", "integration_id", "field_mappings"]

    serializer_field_overrides = {
        "table_id": serializers.IntegerField(
            required=False,
            allow_null=True,
            help_text="The id of the Baserow table we want the data for.",
        ),
        "integration_id": serializers.IntegerField(
            required=False,
            allow_null=True,
            help_text="The id of the Baserow integration we want the data for.",
        ),
        "row_id": FormulaSerializerField(
            required=False,
            allow_blank=True,
            help_text="A formula for defining the intended row.",
        ),
        "field_mappings": LocalBaserowTableServiceFieldMappingSerializer(
            many=True,
            required=False,
            help_text="The field mapping associated with this service.",
        ),
    }

    class SerializedDict(ServiceDict):
        row_id: BaserowFormula
        table_id: int
        field_mappings: List[Dict]

    def after_update(
        self,
        instance: LocalBaserowUpsertRow,
        values: Dict,
        changes: Dict[str, Tuple],
    ):
        """
        Responsible for managing the upsert row's field mappings following
        a successful service update.

        :param instance: The updated service instance.
        :param values: The values that were passed when creating the service
            metadata.
        :param changes: A dictionary containing all changes which were made to the
            service prior to `after_update` being called.
        """

        if "field_mappings" in values and instance.table_id:
            bulk_field_mappings = []
            # Bulk delete the existing field mappings on the service.
            # We'll bulk create the mappings in the values `field_mappings`.
            instance.field_mappings.all().delete()
            # The queryset we'll use to narrow down the `get_field` query,
            # this ensures we find the field within the service's table.
            base_field_qs = instance.table.field_set.all()
            field_mappings = values.get("field_mappings", [])
            for field_mapping in field_mappings:
                try:
                    field = FieldHandler().get_field(
                        field_mapping["field_id"], base_queryset=base_field_qs
                    )
                except KeyError:
                    raise DRFValidationError("A field mapping must have a `field_id`.")
                except FieldDoesNotExist as exc:
                    raise DRFValidationError(str(exc))

                bulk_field_mappings.append(
                    LocalBaserowTableServiceFieldMapping(
                        field=field, service=instance, value=field_mapping["value"]
                    )
                )
            LocalBaserowTableServiceFieldMapping.objects.bulk_create(
                bulk_field_mappings
            )

    def serialize_property(self, service: LocalBaserowUpsertRow, prop_name: str):
        """
        You can customize the behavior of the serialization of a property with this
        hook.
        """

        if prop_name == "field_mappings":
            return [
                {
                    "field_id": m.field_id,
                    "value": m.value,
                }
                for m in service.field_mappings.all()
            ]

        return super().serialize_property(service, prop_name)

    def deserialize_property(
        self, prop_name: str, value: Any, id_mapping: Dict[str, Any], **kwargs
    ):
        """
        Responsible for deserializing the `field_mappings`, if they're present.

        :param prop_name: the name of the property being transformed.
        :param value: the value of this property.
        :param id_mapping: the id mapping dict.
        :return: the deserialized version for this property.
        """

        # Migrate the row id formula
        if prop_name == "row_id":
            return import_formula(value, id_mapping)

        if prop_name == "field_mappings":
            return [
                {
                    "value": import_formula(item["value"], id_mapping),
                    "field_id": (
                        id_mapping["database_fields"][item["field_id"]]
                        if "database_fields" in id_mapping
                        else item["field_id"]
                    ),
                }
                for item in value
            ]

        return super().deserialize_property(prop_name, value, id_mapping, **kwargs)

    def create_instance_from_serialized(self, serialized_values):
        """
        Responsible for creating the service, and then if `field_mappings`
        are present, creating them in bulk.

        :param serialized_values: The serialized service data.
        :return: The newly created service instance.
        """

        field_mappings = serialized_values.pop("field_mappings", [])

        service = super().create_instance_from_serialized(serialized_values)

        # Create the field mappings
        LocalBaserowTableServiceFieldMapping.objects.bulk_create(
            [
                LocalBaserowTableServiceFieldMapping(
                    **field_mapping,
                    service=service,
                )
                for field_mapping in field_mappings
            ]
        )

        return service

    def enhance_queryset(self, queryset):
        return queryset.select_related("table").prefetch_related("field_mappings")

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

    def resolve_service_formulas(
        self,
        service: ServiceSubClass,
        dispatch_context: DispatchContext,
    ) -> Dict[str, Any]:
        """
        :param service: A `LocalBaserowTableService` instance.
        :param dispatch_context: The dispatch_context instance used to
            resolve formulas (if any).
        :raises ServiceImproperlyConfigured: When we try and dispatch a service that
            has no `Table` associated with it.
        """

        resolved_values = super().resolve_service_formulas(service, dispatch_context)

        if not service.row_id:
            # We've received no `row_id` as we're creating a new row.
            resolved_values["row_id"] = service.row_id
            return resolved_values

        try:
            resolved_values["row_id"] = ensure_integer(
                resolve_formula(
                    service.row_id,
                    formula_runtime_function_registry,
                    dispatch_context,
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

        return resolved_values

    def dispatch_data(
        self,
        service: LocalBaserowUpsertRow,
        resolved_values: Dict[str, Any],
        dispatch_context: DispatchContext,
    ) -> Dict[str, Any]:
        """
        Responsible for creating a new row, or updating an existing row if a row ID has
        been provided, in this `LocalBaserowUpsertRow` service's table.

        :param service: the local baserow upsert row service.
        :param resolved_values: If the service has any formulas, this dictionary will
            contain their resolved values.
        :param dispatch_context: the context used for formula resolution.
        :return: The created or updated rows.
        """

        table = resolved_values["table"]
        integration = service.integration.specific

        field_values = {}
        field_mappings = service.field_mappings.select_related("field").all()
        for field_mapping in field_mappings:
            resolved_value = resolve_formula(
                field_mapping.value,
                formula_runtime_function_registry,
                dispatch_context,
            )

            field = field_mapping.field
            field_type = field_type_registry.get_by_model(field.specific_class)

            # Transform and validate the resolved value with the field type's DRF field.
            serializer_field = field_type.get_serializer_field(field.specific)
            resolved_value = serializer_field.run_validation(resolved_value)

            # Then transform and validate the resolved value for prepare value for db.
            try:
                field_values[field.db_column] = field_type.prepare_value_for_db(
                    field.specific, resolved_value
                )
            except ValidationError as exc:
                raise ServiceImproperlyConfigured(
                    "The result value of the formula is not valid for the "
                    f"field `{field.name} ({field.db_column})`: {exc.message}"
                ) from exc

        if resolved_values["row_id"]:
            row = RowHandler().update_row_by_id(
                integration.authorized_user,
                table,
                row_id=resolved_values["row_id"],
                values=field_values,
                values_already_prepared=True,
            )
        else:
            row = RowHandler().create_row(
                user=integration.authorized_user,
                table=table,
                values=field_values,
                values_already_prepared=True,
            )

        return {"data": row, "baserow_table_model": table.get_model()}
