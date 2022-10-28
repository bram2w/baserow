from django.contrib.auth import get_user_model

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from baserow.core.models import GroupUser

User = get_user_model()


class GroupUserSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField(help_text="User defined name.")
    email = serializers.SerializerMethodField(help_text="User email.")
    to_be_deleted = serializers.BooleanField(
        source="user.profile.to_be_deleted",
        help_text="True if user account is pending deletion.",
    )

    class Meta:
        model = GroupUser
        fields = (
            "id",
            "name",
            "email",
            "group",
            "permissions",
            "created_on",
            "user_id",
            "to_be_deleted",
        )

    @extend_schema_field(OpenApiTypes.STR)
    def get_name(self, object):
        return object.user.first_name

    @extend_schema_field(OpenApiTypes.STR)
    def get_email(self, object):
        return object.user.email


class GroupUserGroupSerializer(serializers.Serializer):
    """
    This serializers includes relevant fields of the Group model, but also
    some GroupUser specific fields related to the group user relation.

    Additionally, the list of users are included for each group.
    """

    # Group fields
    id = serializers.IntegerField(
        source="group.id", read_only=True, help_text="Group id."
    )
    name = serializers.CharField(
        source="group.name", read_only=True, help_text="Group name."
    )
    users = GroupUserSerializer(
        many=True,
        source="group.groupuser_set",
        required=False,
        read_only=True,
        help_text="List of all group users.",
    )

    # GroupUser fields
    order = serializers.IntegerField(
        read_only=True, help_text="The requesting user's order within the group users."
    )
    permissions = serializers.CharField(
        read_only=True, help_text="The requesting user's permissions for the group."
    )


class UpdateGroupUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupUser
        fields = ("permissions",)


class GetGroupUsersViewParamsSerializer(serializers.Serializer):
    search = serializers.CharField(required=False, allow_null=True, default=None)
    sorts = serializers.CharField(required=False, allow_null=True, default=None)
