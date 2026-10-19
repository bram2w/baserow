from django.db import transaction

from baserow.contrib.dashboard.handler import DashboardHandler
from baserow.contrib.dashboard.widgets.models import Widget
from baserow.contrib.dashboard.widgets.operations import UpdateWidgetOperationType
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
    def update_filter(self, user, filter_id, **values):
        dashboard_filter = self.handler.get_filter(filter_id, for_update=True)
        CoreHandler().check_permissions(
            user,
            UpdateDashboardFilterOperationType.type,
            workspace=dashboard_filter.dashboard.workspace,
            context=dashboard_filter,
        )
        if "bindings" in values:
            self.validate_bindings(user, dashboard_filter.dashboard, values["bindings"])
            remaining_widgets = [binding["widget_id"] for binding in values["bindings"]]
            for binding in dashboard_filter.bindings.exclude(
                widget_id__in=remaining_widgets
            ).select_related("widget"):
                CoreHandler().check_permissions(
                    user,
                    UpdateWidgetOperationType.type,
                    workspace=dashboard_filter.dashboard.workspace,
                    context=binding.widget.specific,
                )
        previous, updated = self.handler.update_filter(dashboard_filter, **values)
        dashboard_filters_updated.send(
            self, dashboard=dashboard_filter.dashboard, user=user
        )
        return dashboard_filter, previous, updated

    def validate_bindings(self, user, dashboard, bindings):
        widget_ids = [binding["widget_id"] for binding in bindings]
        widgets = {
            widget.id: widget.specific
            for widget in Widget.objects.filter(dashboard=dashboard, id__in=widget_ids)
        }
        if len(widget_ids) != len(set(widget_ids)) or set(widget_ids) != widgets.keys():
            raise DashboardFilterInvalidBinding(
                "Each binding must reference a different widget in this dashboard."
            )
        for binding in bindings:
            widget = widgets[binding["widget_id"]]
            CoreHandler().check_permissions(
                user,
                UpdateWidgetOperationType.type,
                workspace=dashboard.workspace,
                context=widget,
            )
            if binding["field_id"] is None:
                # A missing field remains a broken association, including after undo.
                continue
            field = Field.objects.filter(id=binding["field_id"]).first()
            source = getattr(widget, "data_source", None)
            service = source.service.specific if source and source.service else None
            if field is None or field.table_id != getattr(service, "table_id", None):
                raise DashboardFilterInvalidBinding(
                    "The field must belong to the widget's source table."
                )
            get_text_field_type(field.specific)
