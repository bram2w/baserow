from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import translation

from baserow_premium.api.admin.views import AdminListingView
from baserow_premium.license.handler import LicenseHandler
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.status import HTTP_202_ACCEPTED
from rest_framework.views import APIView

from baserow.api.decorators import (
    map_exceptions,
    validate_body,
    validate_query_parameters,
)
from baserow.api.jobs.errors import ERROR_MAX_JOB_COUNT_EXCEEDED
from baserow.api.jobs.serializers import JobSerializer
from baserow.api.schemas import CLIENT_SESSION_ID_SCHEMA_PARAMETER, get_error_schema
from baserow.core.action.registries import action_type_registry
from baserow.core.jobs.exceptions import MaxJobCountExceeded
from baserow.core.jobs.handler import JobHandler
from baserow.core.jobs.registries import job_type_registry
from baserow.core.models import Group
from baserow_enterprise.audit_log.job_types import AuditLogExportJobType
from baserow_enterprise.audit_log.models import AuditLogEntry
from baserow_enterprise.features import AUDIT_LOG

from .serializers import (
    AuditLogActionTypeSerializer,
    AuditLogExportJobRequestSerializer,
    AuditLogExportJobResponseSerializer,
    AuditLogGroupSerializer,
    AuditLogQueryParamsSerializer,
    AuditLogSerializer,
    AuditLogUserSerializer,
)

User = get_user_model()


class AdminAuditLogView(AdminListingView):
    permission_classes = (IsAdminUser,)
    serializer_class = AuditLogSerializer
    filters_field_mapping = {
        "user_id": "user_id",
        "group_id": "group_id",
        "action_type": "action_type",
        "from_timestamp": "action_timestamp__gte",
        "to_timestamp": "action_timestamp__lte",
        "ip_address": "ip_address",
    }
    sort_field_mapping = {
        "user": "user_email",
        "group": "group_name",
        "type": "action_type",
        "timestamp": "action_timestamp",
        "ip_address": "ip_address",
    }
    default_order_by = "-action_timestamp"

    def get_queryset(self, request):
        return AuditLogEntry.objects.all()

    def get_serializer(self, request, *args, **kwargs):
        return super().get_serializer(
            request, *args, context={"request": request}, **kwargs
        )

    @extend_schema(
        tags=["Admin"],
        operation_id="admin_audit_log",
        description="Lists all audit log entries.",
        **AdminListingView.get_extend_schema_parameters(
            "audit_log_entries", serializer_class, [], sort_field_mapping
        ),
    )
    @validate_query_parameters(AuditLogQueryParamsSerializer)
    def get(self, request, query_params):
        LicenseHandler.raise_if_user_doesnt_have_feature_instance_wide(
            AUDIT_LOG, request.user
        )
        with translation.override(request.user.profile.language):
            return super().get(request)


class AdminAuditLogUserFilterView(AdminListingView):
    permission_classes = (IsAdminUser,)
    serializer_class = AuditLogUserSerializer
    search_fields = ["email"]
    default_order_by = "email"

    def get_queryset(self, request):
        return User.objects.all()

    @extend_schema(
        tags=["Admin"],
        operation_id="admin_audit_log_users",
        description="List all users that have performed an action in the audit log.",
        **AdminListingView.get_extend_schema_parameters(
            "users", serializer_class, search_fields, {}
        ),
    )
    def get(self, request):
        LicenseHandler.raise_if_user_doesnt_have_feature_instance_wide(
            AUDIT_LOG, request.user
        )
        return super().get(request)


class AdminAuditLogGroupFilterView(AdminListingView):
    permission_classes = (IsAdminUser,)
    serializer_class = AuditLogGroupSerializer
    search_fields = ["name"]
    default_order_by = "name"

    def get_queryset(self, request):
        return Group.objects.filter(template__isnull=True)

    @extend_schema(
        tags=["Admin"],
        operation_id="admin_audit_log_groups",
        description="List all distinct group names related to an audit log entry.",
        **AdminListingView.get_extend_schema_parameters(
            "groups", serializer_class, search_fields, {}
        ),
    )
    def get(self, request):
        LicenseHandler.raise_if_user_doesnt_have_feature_instance_wide(
            AUDIT_LOG, request.user
        )
        return super().get(request)


class AdminAuditLogActionTypeFilterView(APIView):
    permission_classes = (IsAdminUser,)
    serializer_class = AuditLogActionTypeSerializer

    def filter_action_types(self, action_types, search):
        search_lower = search.lower()
        return [
            action_type
            for action_type in action_types
            if search_lower in action_type["value"].lower()
        ]

    @extend_schema(
        tags=["Admin"],
        operation_id="admin_audit_log_types",
        description="List all distinct action types related to an audit log entry.",
    )
    def get(self, request):
        LicenseHandler.raise_if_user_doesnt_have_feature_instance_wide(
            AUDIT_LOG, request.user
        )

        # Since action's type is translated at runtime and there aren't that
        # many, we can fetch them all and filter them in memory to match the
        # search query on the translated value.
        with translation.override(request.user.profile.language):
            search = request.GET.get("search")

            action_types = AuditLogActionTypeSerializer(
                action_type_registry.get_all(), many=True
            ).data

            if search:
                action_types = self.filter_action_types(action_types, search)

            return Response(
                {
                    "count": len(action_types),
                    "next": None,
                    "previous": None,
                    "results": sorted(action_types, key=lambda x: x["value"]),
                }
            )


class AsyncAuditLogExportView(APIView):
    permission_classes = (IsAdminUser,)

    @extend_schema(
        parameters=[CLIENT_SESSION_ID_SCHEMA_PARAMETER],
        tags=["Audit log export"],
        operation_id="export_audit_log",
        description=("Creates a job to export the filtered audit log to a CSV file."),
        request=AuditLogExportJobRequestSerializer,
        responses={
            202: AuditLogExportJobResponseSerializer,
            400: get_error_schema(
                ["ERROR_REQUEST_BODY_VALIDATION", "ERROR_MAX_JOB_COUNT_EXCEEDED"]
            ),
        },
    )
    @transaction.atomic
    @map_exceptions({MaxJobCountExceeded: ERROR_MAX_JOB_COUNT_EXCEEDED})
    @validate_body(AuditLogExportJobRequestSerializer)
    def post(self, request, data):
        """Creates a job to export the filtered audit log entries to a CSV file."""

        LicenseHandler.raise_if_user_doesnt_have_feature_instance_wide(
            AUDIT_LOG, request.user
        )

        csv_export_job = JobHandler().create_and_start_job(
            request.user, AuditLogExportJobType.type, **data
        )

        serializer = job_type_registry.get_serializer(
            csv_export_job, JobSerializer, context={"request": request}
        )
        return Response(serializer.data, status=HTTP_202_ACCEPTED)
