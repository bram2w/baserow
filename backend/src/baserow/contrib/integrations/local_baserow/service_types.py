from typing import Any, Dict

from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError

from rest_framework import serializers

from baserow.contrib.database.api.rows.serializers import (
    RowSerializer,
    get_row_serializer_class,
)
from baserow.contrib.database.rows.operations import ReadDatabaseRowOperationType
from baserow.contrib.database.table.handler import TableHandler
from baserow.contrib.database.table.operations import ListRowsDatabaseTableOperationType
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
from baserow.core.services.models import Service
from baserow.core.services.registries import ServiceType
from baserow.core.services.types import ServiceDict
from baserow.formula import resolve_formula


class LocalBaserowListRowsUserServiceType(ServiceType):
    """
    This service gives access to a list of rows from the same Baserow instance as the
    one hosting the application.
    """

    integration_type = LocalBaserowIntegrationType.type
    type = "local_baserow_list_rows"
    model_class = LocalBaserowListRows

    class SerializedDict(ServiceDict):
        table_id: int

    serializer_field_names = ["table_id"]
    allowed_fields = ["table"]

    serializer_field_overrides = {
        "table_id": serializers.IntegerField(
            required=False,
            allow_null=True,
            help_text="The id of the Baserow table we want the data for.",
        ),
    }

    def enhance_queryset(self, queryset):
        return queryset.select_related("table")

    def prepare_values(
        self, values: Dict[str, Any], user: AbstractUser
    ) -> Dict[str, Any]:
        """Load the table instance instead of the ID."""

        if "table_id" in values:
            table_id = values.pop("table_id")
            if table_id is not None:
                table = TableHandler().get_table(table_id)
                values["table"] = table
            else:
                values["table"] = None

        return super().prepare_values(values, user)

    def transform_serialized_value(
        self, prop_name: str, value: Any, id_mapping: Dict[str, Any]
    ):
        """
        Get the table Id from the mapping if it exists.
        """

        if prop_name == "table_id" and "database_tables" in id_mapping:
            return id_mapping["database_tables"].get(value, None)

        return value

    def dispatch(
        self, service: Service, runtime_formula_context: RuntimeFormulaContext
    ):
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
            raise ServiceImproperlyConfigured("The Table property is missing.")

        CoreHandler().check_permissions(
            integration.authorized_user,
            ListRowsDatabaseTableOperationType.type,
            workspace=table.database.workspace,
            context=table,
        )

        model = table.get_model()
        rows = model.objects.all()[:200]

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
        table_id: int
        row_id: str

    serializer_field_names = ["table_id", "row_id"]
    allowed_fields = ["table", "row_id"]

    serializer_field_overrides = {
        "table_id": serializers.IntegerField(
            required=False,
            allow_null=True,
            help_text="The id of the Baserow table we want the data for.",
        ),
        "row_id": FormulaSerializerField(
            required=False,
            allow_blank=True,
            help_text="A formula for defining the intended row.",
        ),
    }

    def enhance_queryset(self, queryset):
        return queryset.select_related(
            "table", "table__database", "table__database__workspace"
        )

    def prepare_values(
        self, values: Dict[str, Any], user: AbstractUser
    ) -> Dict[str, Any]:
        """Load the table instance instead of the ID."""

        if "table_id" in values:
            table_id = values.pop("table_id")
            if table_id is not None:
                table = TableHandler().get_table(table_id)
                values["table"] = table
            else:
                values["table"] = None

        return super().prepare_values(values, user)

    def transform_serialized_value(
        self, prop_name: str, value: Any, id_mapping: Dict[str, Any]
    ):
        """
        Get the table Id from the mapping if it exists.
        """

        if prop_name == "table_id" and "database_tables" in id_mapping:
            return id_mapping["database_tables"].get(value, None)

        return value

    def dispatch(
        self, service: Service, runtime_formula_context: RuntimeFormulaContext
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
