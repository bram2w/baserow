from baserow.contrib.dashboard.data_sources.service import DashboardDataSourceService
from baserow.contrib.dashboard.widgets.service import WidgetService
from baserow.contrib.database.api.rows.serializers import (
    RowSerializer,
    get_row_serializer_class,
)
from baserow.contrib.database.table.exceptions import TableDoesNotExist
from baserow.contrib.database.table.operations import ListRowsDatabaseTableOperationType
from baserow.contrib.database.table.service import TableService
from baserow.core.formula.exceptions import InvalidRuntimeFormula
from baserow.core.handler import CoreHandler


class DashboardTableRecordsService:
    """Read the tables used by visible widgets, independently of their calculations."""

    def get_table(self, user, dashboard, table_id):
        widgets = WidgetService().get_widgets(user, dashboard.id)
        source_ids = {
            widget.specific.data_source_id
            for widget in widgets
            if hasattr(widget.specific, "data_source_id")
        }
        sources = DashboardDataSourceService().get_data_sources(user, dashboard.id)
        if not any(
            source.id in source_ids
            and source.service
            and getattr(source.service.specific, "table_id", None) == table_id
            for source in sources
        ):
            raise InvalidRuntimeFormula("The table is not used by this dashboard.")
        try:
            return self.get_readable_table(user, table_id)
        except TableDoesNotExist as exc:
            raise InvalidRuntimeFormula("The table no longer exists.") from exc

    def get_readable_table(self, user, table_id):
        table = TableService().get_table(user, table_id)
        CoreHandler().check_permissions(
            user,
            ListRowsDatabaseTableOperationType.type,
            workspace=table.database.workspace,
            context=table,
        )
        return table

    def get_records(self, user, dashboard, table_id, field_name=None):
        table = self.get_table(user, dashboard, table_id)
        return DashboardTableRecordsHandler().get_records(table, field_name)


class DashboardTableRecordsHandler:
    def get_records(self, table, field_name=None):
        model = table.get_model()
        field_objects = model.get_field_objects()
        if field_name is not None:
            field_objects = [
                item for item in field_objects if item["name"] == field_name
            ]
            if not field_objects and field_name != "id":
                raise InvalidRuntimeFormula("The table field no longer exists.")
        field_ids = [item["field"].id for item in field_objects]
        queryset = (
            model.objects.all()
            .enhance_by_fields(only_field_ids=field_ids)
            .only("id", "order", *(item["name"] for item in field_objects))
        )
        serializer = get_row_serializer_class(
            model, RowSerializer, is_response=True, field_ids=field_ids
        )
        records = []
        for row in queryset.iterator(chunk_size=2000):
            record = dict(serializer(row).data)
            for item in field_objects:
                name = item["name"]
                record[name] = item["type"].to_runtime_formula_value(
                    item["field"], record[name]
                )
            records.append(record)
        return records
