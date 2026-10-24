from django.db import transaction

from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from baserow.api.decorators import map_exceptions, validate_body
from baserow.contrib.dashboard.api.data_sources.errors import (
    ERROR_DASHBOARD_DATA_DOES_NOT_EXIST,
    ERROR_DASHBOARD_DATA_SOURCE_DOES_NOT_EXIST,
    ERROR_DASHBOARD_DATA_SOURCE_IMPROPERLY_CONFIGURED,
)
from baserow.contrib.dashboard.data_sources.dispatch_context import (
    DashboardDispatchContext,
)
from baserow.contrib.dashboard.data_sources.exceptions import (
    DashboardDataSourceDoesNotExist,
    DashboardDataSourceImproperlyConfigured,
)
from baserow.contrib.dashboard.data_sources.service import DashboardDataSourceService
from baserow.contrib.dashboard.widgets.exceptions import WidgetDoesNotExist
from baserow.contrib.dashboard.widgets.service import WidgetService
from baserow.core.services.exceptions import (
    DoesNotExist,
    ServiceImproperlyConfiguredDispatchException,
)

from .errors import ERROR_WIDGET_DOES_NOT_EXIST


class AppliedDashboardFilterSerializer(serializers.Serializer):
    filter_id = serializers.IntegerField(min_value=1)
    values = serializers.ListField(
        child=serializers.CharField(trim_whitespace=False, allow_blank=True),
    )


class DispatchWidgetSerializer(serializers.Serializer):
    filters = AppliedDashboardFilterSerializer(many=True, required=False, default=list)


class DispatchWidgetView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        tags=["Dashboard widgets"],
        operation_id="dispatch_dashboard_widget",
        request=DispatchWidgetSerializer,
        responses={200: serializers.DictField()},
        description="Calculate a widget using private filter values referenced by its data source formulas.",
    )
    @transaction.atomic
    @map_exceptions(
        {
            WidgetDoesNotExist: ERROR_WIDGET_DOES_NOT_EXIST,
            DashboardDataSourceDoesNotExist: ERROR_DASHBOARD_DATA_SOURCE_DOES_NOT_EXIST,
            DashboardDataSourceImproperlyConfigured: ERROR_DASHBOARD_DATA_SOURCE_IMPROPERLY_CONFIGURED,
            ServiceImproperlyConfiguredDispatchException: ERROR_DASHBOARD_DATA_SOURCE_IMPROPERLY_CONFIGURED,
            DoesNotExist: ERROR_DASHBOARD_DATA_DOES_NOT_EXIST,
        }
    )
    @validate_body(DispatchWidgetSerializer, return_validated=True)
    def post(self, request, widget_id, data):
        widget = WidgetService().get_widget(request.user, widget_id)
        if not getattr(widget, "data_source_id", None):
            raise DashboardDataSourceImproperlyConfigured(
                "This widget has no data source."
            )
        context = DashboardDispatchContext(
            request,
            widget.dashboard.workspace,
            widget=widget,
            applied_filters=data["filters"],
        )
        result = DashboardDataSourceService().dispatch_data_source(
            request.user, widget.data_source_id, context
        )
        return Response(result)
