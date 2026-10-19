from django.db import transaction

from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from baserow.api.decorators import map_exceptions, validate_body
from baserow.contrib.dashboard.api.data_sources.errors import (
    ERROR_DASHBOARD_DATA_SOURCE_IMPROPERLY_CONFIGURED,
)
from baserow.contrib.dashboard.filters.exceptions import (
    DashboardFilterDoesNotExist,
    DashboardFilterInvalidBinding,
)
from baserow.contrib.dashboard.filters.options import DashboardFilterOptionsService
from baserow.core.services.exceptions import (
    ServiceImproperlyConfiguredDispatchException,
)

from .errors import (
    ERROR_DASHBOARD_FILTER_DOES_NOT_EXIST,
    ERROR_DASHBOARD_FILTER_INVALID_BINDING,
)


class DashboardFilterOptionsRequestSerializer(serializers.Serializer):
    search = serializers.CharField(
        required=False,
        default="",
        allow_blank=True,
        trim_whitespace=False,
        max_length=10000,
    )
    after = serializers.CharField(
        required=False, allow_null=True, trim_whitespace=False, max_length=10000
    )
    limit = serializers.IntegerField(min_value=1, max_value=100, default=50)
    selected = serializers.ListField(
        child=serializers.CharField(trim_whitespace=False, max_length=10000),
        required=False,
        default=list,
    )


class DashboardFilterOptionsResponseSerializer(serializers.Serializer):
    results = serializers.ListField(child=serializers.CharField())
    next = serializers.CharField(allow_null=True)
    available = serializers.ListField(child=serializers.CharField())


class DashboardFilterOptionsView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        tags=["Dashboard filters"],
        operation_id="list_dashboard_filter_options",
        request=DashboardFilterOptionsRequestSerializer,
        responses={200: DashboardFilterOptionsResponseSerializer},
        description="List distinct values from the filter's source restrictions. Selected-value availability is independent of search and pagination.",
    )
    @transaction.atomic
    @map_exceptions(
        {
            DashboardFilterDoesNotExist: ERROR_DASHBOARD_FILTER_DOES_NOT_EXIST,
            DashboardFilterInvalidBinding: ERROR_DASHBOARD_FILTER_INVALID_BINDING,
            ServiceImproperlyConfiguredDispatchException: ERROR_DASHBOARD_DATA_SOURCE_IMPROPERLY_CONFIGURED,
        }
    )
    @validate_body(DashboardFilterOptionsRequestSerializer, return_validated=True)
    def post(self, request, filter_id, data):
        return Response(
            DashboardFilterOptionsService().get_options(
                request.user, filter_id, request, **data
            )
        )
