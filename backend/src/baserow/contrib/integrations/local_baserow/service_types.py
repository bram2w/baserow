from typing import Any, Dict, Optional

from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError

from rest_framework import serializers

from baserow.contrib.database.api.rows.serializers import (
    RowSerializer,
    get_row_serializer_class,
)
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
from baserow.core.services.types import ServiceDict


class LocalBaserowListRowsUserServiceType(
    ServiceType,
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

    class SerializedDict(ServiceDict):
        table_id: int
        view_id: int
        search_query: str

    serializer_field_names = ["table_id", "view_id", "search_query"]
    allowed_fields = ["table", "view", "search_query"]

    serializer_field_overrides = {
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
        return queryset.select_related("view__table").prefetch_related(
            "view__viewfilter_set", "view__viewsort_set", "view__viewgroupby_set"
        )

    def prepare_values(
        self, values: Dict[str, Any], user: AbstractUser
    ) -> Dict[str, Any]:
        """Load the table & view instance instead of the ID."""

        if "table_id" in values:
            table_id = values.pop("table_id")
            if table_id is not None:
                table = TableHandler().get_table(table_id)
                values["table"] = table
            else:
                values["table"] = None

        if "view_id" in values:
            view_id = values.pop("view_id")
            if view_id is not None:
                view = ViewHandler().get_view(view_id)
                values["view"] = view
            else:
                values["view"] = None

        return super().prepare_values(values, user)

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
        filter_builder = self.get_dispatch_filters(service, model)
        if filter_builder is not None:
            queryset = filter_builder.apply_to_queryset(queryset)

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
            user_field_names=True,
        )
        return serializer(dispatch_data["data"], many=True).data


class LocalBaserowGetRowUserServiceType(
    ServiceType,
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

    serializer_field_names = ["table_id", "view_id", "row_id", "search_query"]
    allowed_fields = ["table", "view", "row_id", "search_query"]

    serializer_field_overrides = {
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
            "view", "view__table__database", "view__table__database__workspace"
        )

    def prepare_values(
        self, values: Dict[str, Any], user: AbstractUser
    ) -> Dict[str, Any]:
        """Load the table & view instance instead of the ID."""

        if "table_id" in values:
            table_id = values.pop("table_id")
            if table_id is not None:
                table = TableHandler().get_table(table_id)
                values["table"] = table
            else:
                values["table"] = None

        if "view_id" in values:
            view_id = values.pop("view_id")
            if view_id is not None:
                view = ViewHandler().get_view(view_id)
                values["view"] = view
            else:
                values["view"] = None

        return super().prepare_values(values, user)

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
            dispatch_data["baserow_table_model"],
            RowSerializer,
            is_response=True,
            user_field_names=True,
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

        # Find the `ViewFilter` applicable to this Service's View.
        filter_builder = self.get_dispatch_filters(service, model)
        if filter_builder is not None:
            queryset = filter_builder.apply_to_queryset(queryset)

        try:
            row = queryset.get(pk=row_id)
            return {"data": row, "baserow_table_model": model}
        except model.DoesNotExist:
            raise DoesNotExist()
