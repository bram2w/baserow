from django.contrib.auth import get_user_model

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer

from baserow.core.models import Group, GroupUser

User = get_user_model()


class GroupAdminUsersSerializer(ModelSerializer):
    id = serializers.IntegerField(source="user.id")
    email = serializers.CharField(source="user.email")

    class Meta:
        model = GroupUser

        fields = ("id", "email", "permissions")


class GroupsAdminResponseSerializer(ModelSerializer):
    users = GroupAdminUsersSerializer(source="groupuser_set", many=True)
    application_count = serializers.IntegerField()
    row_count = serializers.SerializerMethodField()
    free_users = serializers.SerializerMethodField()
    seats_taken = serializers.IntegerField()

    ROW_COUNT_ANNOTATION_NAME = "row_count"

    @extend_schema_field(OpenApiTypes.INT)
    def get_free_users(self, instance):
        if instance.seats_taken:
            return instance.groupuser_set.count() - instance.seats_taken
        else:
            return None

    @extend_schema_field(OpenApiTypes.INT)
    def get_row_count(self, instance):
        return getattr(instance, self.ROW_COUNT_ANNOTATION_NAME, None)

    class Meta:
        model = Group
        fields = (
            "id",
            "name",
            "users",
            "application_count",
            "row_count",
            "storage_usage",
            "seats_taken",
            "free_users",
            "created_on",
        )
