from rest_framework import serializers

from baserow.core.models import Snapshot, User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("username",)


class SnapshotSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)

    class Meta:
        model = Snapshot
        fields = [
            "id",
            "name",
            "snapshot_from_application",
            "created_at",
            "created_by",
        ]
        read_only_fields = [
            "id",
            "snapshot_from_application",
            "created_at",
            "created_by",
        ]
