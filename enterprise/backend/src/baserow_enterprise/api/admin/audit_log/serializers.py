from django.contrib.auth import get_user_model
from django.utils.functional import lazy

from rest_framework import serializers

from baserow.core.action.registries import action_type_registry
from baserow.core.jobs.registries import job_type_registry
from baserow.core.models import Workspace
from baserow_enterprise.audit_log.job_types import AuditLogExportJobType
from baserow_enterprise.audit_log.models import AuditLogEntry

User = get_user_model()


def render_user(user_id, user_email):
    return f"{user_email} ({user_id})" if user_id else ""


def render_workspace(workspace_id, workspace_name):
    return f"{workspace_name} ({workspace_id})" if workspace_id else ""


def render_action_type(action_type):
    return action_type_registry.get(action_type).get_short_description()


class AuditLogSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    group = serializers.SerializerMethodField()  # GroupDeprecation
    workspace = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    timestamp = serializers.DateTimeField(source="action_timestamp")

    def get_group(self, instance):  # GroupDeprecation
        return self.get_workspace(instance)

    def get_workspace(self, instance):
        return render_workspace(instance.workspace_id, instance.workspace_name)

    def get_user(self, instance):
        return render_user(instance.user_id, instance.user_email)

    def get_type(self, instance):
        return instance.type

    def get_description(self, instance):
        return instance.description

    class Meta:
        model = AuditLogEntry
        fields = (
            "id",
            "action_type",
            "user",
            "group",  # GroupDeprecation
            "workspace",
            "type",
            "description",
            "timestamp",
            "ip_address",
        )
        read_only_fields = fields


class AuditLogUserSerializer(serializers.ModelSerializer):
    value = serializers.CharField(source="email")

    class Meta:
        model = User
        fields = ("id", "value")


class AuditLogWorkspaceSerializer(serializers.ModelSerializer):
    value = serializers.CharField(source="name")

    class Meta:
        model = Workspace
        fields = ("id", "value")


class AuditLogActionTypeSerializer(serializers.Serializer):
    id = serializers.ChoiceField(
        choices=lazy(action_type_registry.get_types, list)(),
        source="type",
    )
    value = serializers.SerializerMethodField()

    def get_value(self, instance):
        return render_action_type(instance.type)


AuditLogExportJobRequestSerializer = job_type_registry.get(
    AuditLogExportJobType.type
).get_serializer_class(base_class=serializers.Serializer, request_serializer=True)

AuditLogExportJobResponseSerializer = job_type_registry.get(
    AuditLogExportJobType.type
).get_serializer_class(base_class=serializers.Serializer)


class AuditLogQueryParamsSerializer(serializers.Serializer):
    page = serializers.IntegerField(required=False, default=1)
    search = serializers.CharField(required=False, default=None)
    sorts = serializers.CharField(required=False, default=None)
    user_id = serializers.IntegerField(min_value=0, required=False, default=None)
    workspace_id = serializers.IntegerField(min_value=0, required=False, default=None)
    action_type = serializers.ChoiceField(
        choices=lazy(action_type_registry.get_types, list)(),
        default=None,
        required=False,
    )
    from_timestamp = serializers.DateTimeField(required=False, default=None)
    to_timestamp = serializers.DateTimeField(required=False, default=None)
