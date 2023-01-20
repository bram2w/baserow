from django.contrib.auth import get_user_model
from django.utils.functional import lazy

from rest_framework import serializers

from baserow.core.action.registries import action_type_registry
from baserow.core.jobs.registries import job_type_registry
from baserow.core.models import Group
from baserow_enterprise.audit_log.job_types import AuditLogExportJobType
from baserow_enterprise.audit_log.models import AuditLogEntry

User = get_user_model()


def render_user(user_id, user_email):
    return f"{user_email} ({user_id})" if user_id else ""


def render_group(group_id, group_name):
    return f"{group_name} ({group_id})" if group_id else ""


def render_action_type(action_type):
    return action_type_registry.get(action_type).get_short_description()


class AuditLogSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    group = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    timestamp = serializers.DateTimeField(source="action_timestamp")

    def get_group(self, instance):
        return render_group(instance.group_id, instance.group_name)

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
            "group",
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


class AuditLogGroupSerializer(serializers.ModelSerializer):
    value = serializers.CharField(source="name")

    class Meta:
        model = Group
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
    group_id = serializers.IntegerField(min_value=0, required=False, default=None)
    action_type = serializers.ChoiceField(
        choices=lazy(action_type_registry.get_types, list)(),
        default=None,
        required=False,
    )
    from_timestamp = serializers.DateTimeField(required=False, default=None)
    to_timestamp = serializers.DateTimeField(required=False, default=None)
