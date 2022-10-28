from rest_framework import serializers

from baserow.core.models import Group

from .users.serializers import GroupUserGroupSerializer, GroupUserSerializer

__all__ = [
    "GroupUserGroupSerializer",
    "GroupSerializer",
    "OrderGroupsSerializer",
    "GroupUserSerializer",
]


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = (
            "id",
            "name",
        )
        extra_kwargs = {"id": {"read_only": True}}


class PermissionObjectSerializer(serializers.Serializer):
    name = serializers.CharField(help_text="The permission manager name.")
    permissions = serializers.JSONField(
        help_text="The content of the permission object for this permission manager."
    )


class OrderGroupsSerializer(serializers.Serializer):
    groups = serializers.ListField(
        child=serializers.IntegerField(), help_text="Group ids in the desired order."
    )
