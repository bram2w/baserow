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
)
from baserow.contrib.dashboard.filters.options import DashboardFilterOptionsService
from baserow.core.services.exceptions import (
    ServiceImproperlyConfiguredDispatchException,
)

from .errors import (
    ERROR_DASHBOARD_FILTER_DOES_NOT_EXIST,
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
        required=False, allow_null=True, trim_whitespace=False
    )
    limit = serializers.IntegerField(min_value=1, max_value=100, default=50)
    selected = serializers.ListField(
        child=serializers.CharField(trim_whitespace=False),
        required=False,
        default=list,
    )


class DashboardFilterOptionsResponseSerializer(serializers.Serializer):
    results = serializers.ListField(child=serializers.CharField())
    labels = serializers.DictField(child=serializers.CharField())
    next = serializers.CharField(allow_null=True)
    available = serializers.ListField(child=serializers.CharField())


class DashboardFilterOptionsView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        tags=["Dashboard filters"],
        operation_id="list_dashboard_filter_options",
        request=DashboardFilterOptionsRequestSerializer,
        responses={200: DashboardFilterOptionsResponseSerializer},
        description="List manual or formula-based options. Selected-value availability is independent of search and pagination.",
    )
    @transaction.atomic
    @map_exceptions(
        {
            DashboardFilterDoesNotExist: ERROR_DASHBOARD_FILTER_DOES_NOT_EXIST,
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
