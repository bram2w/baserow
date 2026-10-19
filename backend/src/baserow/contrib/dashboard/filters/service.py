from django.db import transaction

from baserow.contrib.dashboard.handler import DashboardHandler
from baserow.contrib.dashboard.widgets.service import WidgetService
from baserow.contrib.database.fields.models import Field
from baserow.core.handler import CoreHandler
from baserow.core.trash.handler import TrashHandler

from .exceptions import DashboardFilterInvalidBinding
from .field_types import get_text_field_type
from .handler import DashboardFilterHandler
from .operations import (
    CreateDashboardFilterOperationType,
    DeleteDashboardFilterOperationType,
    ListDashboardFiltersOperationType,
    ReadDashboardFilterOperationType,
    UpdateDashboardFilterOperationType,
)
from .signals import dashboard_filters_updated


class DashboardFilterService:
    def __init__(self):
        self.handler = DashboardFilterHandler()

    def get_filter(self, user, filter_id):
        dashboard_filter = self.handler.get_filter(filter_id)
        CoreHandler().check_permissions(
            user,
            ReadDashboardFilterOperationType.type,
            workspace=dashboard_filter.dashboard.workspace,
            context=dashboard_filter,
        )
        return dashboard_filter

    def get_filters(self, user, dashboard_id):
        dashboard = DashboardHandler().get_dashboard(dashboard_id)
        CoreHandler().check_permissions(
            user,
            ListDashboardFiltersOperationType.type,
            workspace=dashboard.workspace,
            context=dashboard,
        )
        return CoreHandler().filter_queryset(
            user,
            ListDashboardFiltersOperationType.type,
            self.handler.get_filters(dashboard),
            workspace=dashboard.workspace,
        )

    @transaction.atomic
    def create_filter(self, user, dashboard_id, **values):
        dashboard = DashboardHandler().get_dashboard(dashboard_id)
        CoreHandler().check_permissions(
            user,
            CreateDashboardFilterOperationType.type,
            workspace=dashboard.workspace,
            context=dashboard,
        )
        self.validate_bindings(user, dashboard, values.get("bindings", []))
        dashboard_filter = self.handler.create_filter(dashboard, **values)
        dashboard_filters_updated.send(self, dashboard=dashboard, user=user)
        return dashboard_filter

    @transaction.atomic
    def delete_filter(self, user, filter_id):
        dashboard_filter = self.handler.get_filter(filter_id, for_update=True)
        dashboard = dashboard_filter.dashboard
        CoreHandler().check_permissions(
            user,
            DeleteDashboardFilterOperationType.type,
            workspace=dashboard.workspace,
            context=dashboard_filter,
        )
        TrashHandler.trash(user, dashboard.workspace, dashboard, dashboard_filter)
        dashboard_filters_updated.send(self, dashboard=dashboard, user=user)
        return dashboard_filter

    def restore_filter(self, user, filter_id):
        return TrashHandler.restore_item(user, "dashboard_filter", filter_id)

    @transaction.atomic
    def update_filter(self, user, filter_id, *, restore_bindings=False, **values):
        dashboard_filter = self.handler.get_filter(filter_id, for_update=True)
        CoreHandler().check_permissions(
            user,
            UpdateDashboardFilterOperationType.type,
            workspace=dashboard_filter.dashboard.workspace,
            context=dashboard_filter,
        )
        if "bindings" in values:
            if restore_bindings:
                # Only undo/redo replays server-owned history. Preserve broken
                # mappings while still enforcing the filter's update permission.
                values["bindings"] = self.handler.normalize_binding_references(
                    values["bindings"]
                )
            else:
                self.validate_bindings(
                    user,
                    dashboard_filter.dashboard,
                    values["bindings"],
                    existing=dict(
                        dashboard_filter.bindings.values_list("table_id", "field_id")
                    ),
                )
        previous, updated = self.handler.update_filter(dashboard_filter, **values)
        dashboard_filters_updated.send(
            self, dashboard=dashboard_filter.dashboard, user=user
        )
        return dashboard_filter, previous, updated

    def validate_bindings(self, user, dashboard, bindings, existing=None):
        existing = existing or {}
        table_ids = [binding["table_id"] for binding in bindings]
        if len(table_ids) != len(set(table_ids)):
            raise DashboardFilterInvalidBinding(
                "Choose only one field per table for a dashboard filter."
            )
        # Retain mappings when the last widget using a table is removed, so that
        # a later widget automatically inherits the global filter configuration.
        allowed_tables = set(
            dashboard.filters.values_list("bindings__table_id", flat=True)
        )
        for widget in WidgetService().get_widgets(user, dashboard.id):
            source = getattr(widget, "data_source", None)
            if source and source.service:
                allowed_tables.add(getattr(source.service.specific, "table_id", None))
        if not set(table_ids).issubset(allowed_tables):
            raise DashboardFilterInvalidBinding(
                "The table must be used by this dashboard."
            )
        for binding in bindings:
            # Broken saved mappings remain errors at dispatch, but must not prevent
            # repairing another table's field in the global settings.
            if (
                binding["table_id"] in existing
                and existing[binding["table_id"]] == binding["field_id"]
            ):
                continue
            if binding["field_id"] is None:
                # A missing field remains a broken association, including after undo.
                continue
            field = Field.objects.filter(id=binding["field_id"]).first()
            if field is None or field.table_id != binding["table_id"]:
                raise DashboardFilterInvalidBinding(
                    "The field must belong to the configured table."
                )
            get_text_field_type(field.specific)
