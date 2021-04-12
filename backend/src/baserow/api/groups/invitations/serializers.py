from drf_spectacular.utils import extend_schema_field
from drf_spectacular.openapi import OpenApiTypes

from rest_framework import serializers

from baserow.core.models import GroupInvitation


class GroupInvitationSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupInvitation
        fields = ("id", "group", "email", "permissions", "message", "created_on")
        extra_kwargs = {"id": {"read_only": True}}


class CreateGroupInvitationSerializer(serializers.ModelSerializer):
    base_url = serializers.URLField(
        help_text="The base URL where the user can publicly accept his invitation."
        "The accept token is going to be appended to the base_url (base_url "
        "'/token')."
    )

    class Meta:
        model = GroupInvitation
        fields = ("email", "permissions", "message", "base_url")


class UpdateGroupInvitationSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupInvitation
        fields = ("permissions",)


class UserGroupInvitationSerializer(serializers.ModelSerializer):
    """
    This serializer is used for displaying the invitation to the user that doesn't
    have access to the group yet, so not for invitation management purposes.
    """

    invited_by = serializers.SerializerMethodField()
    group = serializers.SerializerMethodField()
    email_exists = serializers.SerializerMethodField()

    class Meta:
        model = GroupInvitation
        fields = (
            "id",
            "invited_by",
            "group",
            "email",
            "message",
            "created_on",
            "email_exists",
        )
        extra_kwargs = {
            "id": {"read_only": True},
            "message": {"read_only": True},
            "created_on": {"read_only": True},
        }

    @extend_schema_field(OpenApiTypes.STR)
    def get_invited_by(self, object):
        return object.invited_by.first_name

    @extend_schema_field(OpenApiTypes.STR)
    def get_group(self, object):
        return object.group.name

    @extend_schema_field(OpenApiTypes.BOOL)
    def get_email_exists(self, object):
        return object.email_exists if hasattr(object, "email_exists") else None
