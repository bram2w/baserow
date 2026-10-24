from django.db import transaction

from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from baserow.api.decorators import map_exceptions, validate_body
from baserow.api.schemas import (
    CLIENT_SESSION_ID_SCHEMA_PARAMETER,
    CLIENT_UNDO_REDO_ACTION_GROUP_ID_SCHEMA_PARAMETER,
    get_error_schema,
)
from baserow.contrib.dashboard.api.errors import ERROR_DASHBOARD_DOES_NOT_EXIST
from baserow.contrib.dashboard.exceptions import DashboardDoesNotExist
from baserow.contrib.dashboard.filters.actions import (
    CreateDashboardFilterActionType,
    DeleteDashboardFilterActionType,
    UpdateDashboardFilterActionType,
)
from baserow.contrib.dashboard.filters.exceptions import (
    DashboardFilterDoesNotExist,
)
from baserow.contrib.dashboard.filters.service import DashboardFilterService

from .errors import (
    ERROR_DASHBOARD_FILTER_DOES_NOT_EXIST,
)
from .serializers import DashboardFilterSerializer


class DashboardFiltersView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        tags=["Dashboard filters"],
        operation_id="list_dashboard_filters",
        description="List the saved filter configuration, without visitor selections.",
        responses={
            200: DashboardFilterSerializer(many=True),
            404: get_error_schema(["ERROR_DASHBOARD_DOES_NOT_EXIST"]),
        },
    )
    @map_exceptions(
        {
            DashboardDoesNotExist: ERROR_DASHBOARD_DOES_NOT_EXIST,
        }
    )
    def get(self, request, dashboard_id):
        filters = DashboardFilterService().get_filters(request.user, dashboard_id)
        return Response(DashboardFilterSerializer(filters, many=True).data)

    @extend_schema(
        tags=["Dashboard filters"],
        operation_id="create_dashboard_filter",
        description="Create a Text filter for a dashboard.",
        parameters=[
            CLIENT_SESSION_ID_SCHEMA_PARAMETER,
            CLIENT_UNDO_REDO_ACTION_GROUP_ID_SCHEMA_PARAMETER,
        ],
        request=DashboardFilterSerializer,
        responses={
            200: DashboardFilterSerializer,
            400: get_error_schema(["ERROR_REQUEST_BODY_VALIDATION"]),
            404: get_error_schema(["ERROR_DASHBOARD_DOES_NOT_EXIST"]),
        },
    )
    @transaction.atomic
    @map_exceptions(
        {
            DashboardDoesNotExist: ERROR_DASHBOARD_DOES_NOT_EXIST,
        }
    )
    @validate_body(DashboardFilterSerializer, return_validated=True)
    def post(self, request, dashboard_id, data):
        dashboard_filter = CreateDashboardFilterActionType.do(
            request.user, dashboard_id, data
        )
        return Response(DashboardFilterSerializer(dashboard_filter).data)


class DashboardFilterView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        tags=["Dashboard filters"],
        operation_id="update_dashboard_filter",
        description="Update the shared configuration of a dashboard filter.",
        parameters=[
            CLIENT_SESSION_ID_SCHEMA_PARAMETER,
            CLIENT_UNDO_REDO_ACTION_GROUP_ID_SCHEMA_PARAMETER,
        ],
        request=DashboardFilterSerializer,
        responses={
            200: DashboardFilterSerializer,
            404: get_error_schema(["ERROR_DASHBOARD_FILTER_DOES_NOT_EXIST"]),
        },
    )
    @transaction.atomic
    @map_exceptions(
        {
            DashboardFilterDoesNotExist: ERROR_DASHBOARD_FILTER_DOES_NOT_EXIST,
        }
    )
    @validate_body(DashboardFilterSerializer, partial=True, return_validated=True)
    def patch(self, request, filter_id, data):
        dashboard_filter = UpdateDashboardFilterActionType.do(
            request.user, filter_id, data
        )
        return Response(DashboardFilterSerializer(dashboard_filter).data)

    @extend_schema(
        tags=["Dashboard filters"],
        operation_id="delete_dashboard_filter",
        description="Delete a dashboard filter. Its configuration can be restored with undo.",
        parameters=[
            CLIENT_SESSION_ID_SCHEMA_PARAMETER,
            CLIENT_UNDO_REDO_ACTION_GROUP_ID_SCHEMA_PARAMETER,
        ],
        responses={
            204: None,
            404: get_error_schema(["ERROR_DASHBOARD_FILTER_DOES_NOT_EXIST"]),
        },
    )
    @transaction.atomic
    @map_exceptions(
        {DashboardFilterDoesNotExist: ERROR_DASHBOARD_FILTER_DOES_NOT_EXIST}
    )
    def delete(self, request, filter_id):
        DeleteDashboardFilterActionType.do(request.user, filter_id)
        return Response(status=204)
