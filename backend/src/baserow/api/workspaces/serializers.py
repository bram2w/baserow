from rest_framework import serializers

from baserow.core.models import Workspace

from .users.serializers import WorkspaceUserSerializer, WorkspaceUserWorkspaceSerializer

__all__ = [
    "WorkspaceUserWorkspaceSerializer",
    "WorkspaceSerializer",
    "OrderWorkspacesSerializer",
    "WorkspaceUserSerializer",
]


class WorkspaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Workspace
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


class OrderWorkspacesSerializer(serializers.Serializer):
    workspaces = serializers.ListField(
        child=serializers.IntegerField(),
        help_text="Workspace ids in the desired " "order.",
    )
