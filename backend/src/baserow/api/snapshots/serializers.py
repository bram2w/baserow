from rest_framework import serializers

from baserow.core.models import User, Snapshot


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("username",)


class SnapshotSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)

    class Meta:
        model = Snapshot
        fields = ["id", "name", "snapshot_from_application", "created_by", "created_at"]
        read_only_fields = [
            "id",
            "snapshot_from_application",
            "created_by",
            "created_at",
        ]
