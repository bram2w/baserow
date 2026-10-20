from typing import TYPE_CHECKING, Optional

from django.http import HttpRequest

from baserow.contrib.dashboard.data_providers import (
    dashboard_data_provider_type_registry,
)
from baserow.core.services.dispatch_context import DispatchContext

if TYPE_CHECKING:
    from baserow.contrib.dashboard.widgets.models import Widget
    from baserow.core.models import Workspace


class DashboardDispatchContext(DispatchContext):
    own_properties = [
        "request",
        "widget",
        "workspace",
        "applied_filters",
        "dashboard",
    ]
    data_provider_registry = dashboard_data_provider_type_registry

    def __init__(
        self,
        request: HttpRequest,
        workspace: Optional["Workspace"] = None,
        widget: Optional["Widget"] = None,
        applied_filters: list[dict] | None = None,
        dashboard=None,
    ):
        """Create a context for dispatching a dashboard data source."""

        # Before dashboard data sources needed their workspace directly, the second
        # positional argument was the widget. Keep accepting that shape while callers
        # move to passing the workspace.
        if widget is None and workspace is not None and hasattr(workspace, "dashboard"):
            widget = workspace
            workspace = widget.dashboard.workspace

        self.request = request
        self.widget = widget
        self.applied_filters = applied_filters or []
        self.dashboard = dashboard or (widget.dashboard if widget else None)

        super().__init__(workspace)
