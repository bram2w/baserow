from typing import TYPE_CHECKING, Any, Dict, List, Optional, Type

from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db.models.expressions import OrderBy

from rest_framework import serializers

from baserow.contrib.database.api.rows.serializers import (
    RowSerializer,
    get_row_serializer_class,
)
from baserow.contrib.database.rows.operations import ReadDatabaseRowOperationType
from baserow.contrib.database.table.operations import ListRowsDatabaseTableOperationType
from baserow.contrib.database.views.handler import ViewHandler
from baserow.contrib.integrations.local_baserow.integration_types import (
    LocalBaserowIntegrationType,
)
from baserow.contrib.integrations.local_baserow.models import (
    LocalBaserowGetRow,
    LocalBaserowListRows,
)
from baserow.core.formula.registries import formula_runtime_function_registry
from baserow.core.formula.runtime_formula_context import RuntimeFormulaContext
from baserow.core.formula.serializers import FormulaSerializerField
from baserow.core.formula.validator import ensure_integer
from baserow.core.handler import CoreHandler
from baserow.core.services.exceptions import DoesNotExist, ServiceImproperlyConfigured
from baserow.core.services.registries import ListServiceType, ServiceType
from baserow.core.services.types import ServiceDict
from baserow.formula import resolve_formula

if TYPE_CHECKING:
    from baserow.contrib.database.fields.field_filters import FilterBuilder
    from baserow.contrib.database.table.models import GeneratedTableModel


class LocalBaserowListRowsUserServiceType(ListServiceType):
    """
    This service gives access to a list of rows from the same Baserow instance as the
    one hosting the application.
    """

    integration_type = LocalBaserowIntegrationType.type
    type = "local_baserow_list_rows"
    model_class = LocalBaserowListRows
    max_result_limit = 200

    class SerializedDict(ServiceDict):
        view_id: int

    serializer_field_names = ["view_id"]
    allowed_fields = ["view"]

    serializer_field_overrides = {
        "view_id": serializers.IntegerField(
            required=False,
            allow_null=True,
            help_text="The id of the Baserow view we want the data for.",
        ),
    }

    def enhance_queryset(self, queryset):
        return queryset.select_related("view__table").prefetch_related(
            "view__viewfilter_set", "view__viewsort_set"
        )

    def get_dispatch_list_filters(
        self,
        service: LocalBaserowListRows,
        model: Optional[Type["GeneratedTableModel"]] = None,
    ) -> "FilterBuilder":
        """
        Responsible for defining how the `LocalBaserowListRows` service should be
        filtered. All the integration's services point to a Baserow `View`, which
        can have zero or more `ViewFilter` records related to it. We'll use the
        `FilterBuilder` to return a set of filters we can apply to the base queryset.

        :param service: The `LocalBaserow` service we're dispatching.
        :param model: The `service.view.table`'s `GeneratedTableModel`.
        :return: A `FilterBuilder` applicable to the service's view.
        """

        view = service.view
        if model is None:
            model = view.table.get_model()
        return ViewHandler().get_filter_builder(view, model)

    def get_dispatch_list_sorts(
        self,
        service: LocalBaserowListRows,
        model: Optional[Type["GeneratedTableModel"]] = None,
    ) -> List[OrderBy]:
        """
        Responsible for defining how `LocalBaserowIntegration` services should be
        sorted. All the integration's services point to a Baserow `View`, which
        can have zero or more `ViewSort` records related to it. We'll use the
        `ViewHandler.extract_view_sorts` method to return a set of `OrderBy` and
         field name string which we can apply to the base queryset.

        :param service: The `LocalBaserow` service we're dispatching.
        :param model: The `service.view.table`'s `GeneratedTableModel`.
        :return: A list of `OrderBy` expressions.
        """

        view = service.view
        if model is None:
            model = view.table.get_model()
        service_sorts, _ = ViewHandler().extract_view_sorts(view, model)
        return service_sorts

    def prepare_values(
        self, values: Dict[str, Any], user: AbstractUser
    ) -> Dict[str, Any]:
        """Load the View instance instead of the ID."""

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
        Get the view Id from the mapping if it exists.
        """

        if prop_name == "view_id" and "database_tables" in id_mapping:
            return id_mapping["database_tables"].get(value, None)

        return value

    def dispatch(
        self,
        service: LocalBaserowListRows,
        runtime_formula_context: RuntimeFormulaContext,
    ):
        """
        Returns a list of rows from the table stored in the service instance.

        :param service: the local baserow get row service.
        :param runtime_formula_context: the context used for formula resolution.
        :raise ServiceImproperlyConfigured: if the table property is missing.
        :return: The list of rows.
        """

        integration = service.integration.specific

        if service.view is None:
            raise ServiceImproperlyConfigured("The View property is missing.")
        table = service.view.table

        CoreHandler().check_permissions(
            integration.authorized_user,
            ListRowsDatabaseTableOperationType.type,
            workspace=table.database.workspace,
            context=table,
        )

        model = table.get_model()
        queryset = model.objects.all().enhance_by_fields()

        filter_builder = self.get_dispatch_list_filters(service, model)
        queryset = filter_builder.apply_to_queryset(queryset)

        service_sorts = self.get_dispatch_list_sorts(service, model)
        queryset = queryset.order_by(*service_sorts)

        rows = queryset[: self.default_result_limit]

        serializer = get_row_serializer_class(
            model,
            RowSerializer,
            is_response=True,
            user_field_names=True,
        )
        serialized_rows = serializer(rows, many=True).data

        return serialized_rows


class LocalBaserowGetRowUserServiceType(ServiceType):
    """
    This service gives access to one specific row from a given table from the same
    Baserow instance as the one hosting the application.
    """

    integration_type = LocalBaserowIntegrationType.type
    type = "local_baserow_get_row"
    model_class = LocalBaserowGetRow

    class SerializedDict(ServiceDict):
        view_id: int
        row_id: str

    serializer_field_names = ["view_id", "row_id"]
    allowed_fields = ["view", "row_id"]

    serializer_field_overrides = {
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
    }

    def enhance_queryset(self, queryset):
        return queryset.select_related(
            "view", "view__table__database", "view__table__database__workspace"
        )

    def prepare_values(
        self, values: Dict[str, Any], user: AbstractUser
    ) -> Dict[str, Any]:
        """Load the view instance instead of the ID."""

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
        Get the view Id from the mapping if it exists.
        """

        if prop_name == "view_id" and "database_tables" in id_mapping:
            return id_mapping["database_tables"].get(value, None)

        return value

    def dispatch(
        self,
        service: LocalBaserowGetRow,
        runtime_formula_context: RuntimeFormulaContext,
    ):
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

        if service.view is None:
            raise ServiceImproperlyConfigured("The view property is missing.")
        table = service.view.table

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
        try:
            row = model.objects.get(pk=row_id)
        except model.DoesNotExist:
            raise DoesNotExist()

        serializer = get_row_serializer_class(
            model,
            RowSerializer,
            is_response=True,
            user_field_names=True,
        )
        serialized_row = serializer(row).data

        return serialized_row
