from django.db.models import F, TextField
from django.db.models.functions import Cast, Collate

from baserow.contrib.dashboard.data_sources.dispatch_context import (
    DashboardDispatchContext,
)
from baserow.contrib.dashboard.data_sources.operations import (
    DispatchDashboardDataSourceOperationType,
)
from baserow.contrib.dashboard.widgets.service import WidgetService
from baserow.contrib.integrations.local_baserow.service_types import (
    LocalBaserowTableServiceType,
)
from baserow.core.handler import CoreHandler
from baserow.core.services.registries import service_type_registry

from .exceptions import DashboardFilterInvalidBinding
from .field_types import text_field_expression
from .runtime import get_binding_field
from .service import DashboardFilterService


class DashboardFilterOptionsService:
    def get_options(
        self,
        user,
        filter_id,
        request,
        *,
        search="",
        after=None,
        limit=50,
        selected=None,
    ):
        configuration = DashboardFilterService().get_filter(user, filter_id)
        widgets = {
            widget.id: widget
            for widget in WidgetService().get_widgets(user, configuration.dashboard_id)
        }
        context = DashboardDispatchContext(request, configuration.dashboard.workspace)
        choices, available = [], []
        visited_sources = set()
        for binding in configuration.bindings.filter(
            widget_id__in=widgets
        ).select_related("field"):
            widget = widgets[binding.widget_id]
            source = getattr(widget, "data_source", None)
            if source is None or source.trashed or source.service is None:
                raise DashboardFilterInvalidBinding(
                    "The widget has no usable data source."
                )
            CoreHandler().check_permissions(
                user,
                DispatchDashboardDataSourceOperationType.type,
                workspace=configuration.dashboard.workspace,
                context=source,
            )
            service = source.service.specific
            field = get_binding_field(binding, service)
            source_key = (service.id, field.id)
            if source_key in visited_sources:
                continue
            visited_sources.add(source_key)
            service_type = service_type_registry.get_by_model(service)
            if not isinstance(service_type, LocalBaserowTableServiceType):
                raise DashboardFilterInvalidBinding(
                    "This data source does not support text filter options."
                )
            # Validate the source and resolve it with its integration identity. Build
            # the same restricted queryset as dispatch, without dynamic selections.
            service_type.resolve_service_formulas(service, context)
            queryset = service_type.build_queryset(service, service.table, context)
            queryset = (
                queryset.annotate(
                    dashboard_option_text=Cast(
                        text_field_expression(field), TextField()
                    ),
                )
                .annotate(dashboard_option=Collate(F("dashboard_option_text"), "C"))
                .exclude(dashboard_option__isnull=True)
                .exclude(dashboard_option__regex=r"^\s*$")
                .order_by()
            )
            if selected:
                available.append(
                    queryset.filter(dashboard_option__in=selected)
                    .values_list("dashboard_option", flat=True)
                    .distinct()
                )
            if search:
                queryset = queryset.filter(dashboard_option_text__icontains=search)
            if after is not None:
                queryset = queryset.filter(dashboard_option__gt=after)
            choices.append(
                queryset.values_list("dashboard_option", flat=True).distinct()
            )

        results = (
            list(
                choices[0].union(*choices[1:]).order_by("dashboard_option")[: limit + 1]
            )
            if choices
            else []
        )
        selected_available = (
            list(available[0].union(*available[1:]).order_by("dashboard_option"))
            if available
            else []
        )
        return {
            "results": results[:limit],
            "next": results[limit - 1] if len(results) > limit else None,
            "available": selected_available,
        }
