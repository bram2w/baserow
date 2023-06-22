from typing import Any, Dict

from django.contrib.auth.models import AbstractUser

from rest_framework import serializers

from baserow.contrib.database.api.rows.serializers import (
    RowSerializer,
    get_row_serializer_class,
)
from baserow.contrib.database.rows.operations import ReadDatabaseRowOperationType
from baserow.contrib.database.table.handler import TableHandler
from baserow.contrib.database.table.operations import ListRowsDatabaseTableOperationType
from baserow.contrib.integrations.local_baserow.integration_type import (
    LocalBaserowIntegrationType,
)
from baserow.contrib.integrations.local_baserow.models import (
    LocalBaserowGetRow,
    LocalBaserowListRows,
)
from baserow.core.expression import execute_expression
from baserow.core.expression.serializers import ExpressionSerializer
from baserow.core.handler import CoreHandler
from baserow.core.services.registries import ServiceType


class LocalBaserowListRowsUserServiceType(ServiceType):
    integration_type = LocalBaserowIntegrationType.type
    type = "local_baserow_list_rows"
    model_class = LocalBaserowListRows

    serializer_field_names = ["table_id"]
    allowed_fields = ["table"]

    serializer_field_overrides = {
        "table_id": serializers.IntegerField(
            required=False,
            allow_null=True,
            help_text="The id of the Baserow table we want the data for.",
        ),
    }

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

    def dispatch(self, instance):
        table = instance.table
        integration = instance.integration

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

    def import_serialized(
        self, parent: Any, serialized_values: Dict[str, Any], id_mapping: Dict
    ) -> Any:
        return super().import_serialized(parent, serialized_values, id_mapping)

    def export_serialized(self, instance: Any) -> Dict[str, Any]:
        return super().export_serialized(instance)


class LocalBaserowGetRowUserServiceType(ServiceType):
    integration_type = LocalBaserowIntegrationType.type
    type = "local_baserow_get_row"
    model_class = LocalBaserowGetRow

    serializer_field_names = ["table_id", "row_id"]
    allowed_fields = ["table", "row_id"]

    serializer_field_overrides = {
        "table_id": serializers.IntegerField(
            required=False,
            allow_null=True,
            help_text="The id of the Baserow table we want the data for.",
        ),
        "row_id": ExpressionSerializer(
            required=False,
            allow_blank=True,
            help_text="The specific row we want to query.",
        ),
    }

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

    def dispatch(self, instance, data_ledger):
        table = instance.table
        integration = instance.integration
        row_id = execute_expression(instance.row_id, data_ledger)

        CoreHandler().check_permissions(
            integration.authorized_user,
            ReadDatabaseRowOperationType.type,
            workspace=table.database.workspace,
            context=table,
        )

        model = table.get_model()
        row = model.objects.get(pk=row_id)

        serializer = get_row_serializer_class(
            model,
            RowSerializer,
            is_response=True,
            user_field_names=True,
        )
        serialized_row = serializer(row).data

        return serialized_row

    def import_serialized(
        self, parent: Any, serialized_values: Dict[str, Any], id_mapping: Dict
    ) -> Any:
        return super().import_serialized(parent, serialized_values, id_mapping)

    def export_serialized(self, instance: Any) -> Dict[str, Any]:
        return super().export_serialized(instance)
