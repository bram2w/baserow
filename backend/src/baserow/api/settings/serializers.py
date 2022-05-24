from rest_framework import serializers

from baserow.core.models import Settings


class SettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Settings
        fields = (
            "allow_new_signups",
            "allow_signups_via_group_invitations",
            "allow_reset_password",
        )
        extra_kwargs = {
            "allow_new_signups": {"required": False},
            "allow_signups_via_group_invitations": {"required": False},
            "allow_reset_password": {"required": False},
        }


class InstanceIdSerializer(serializers.ModelSerializer):
    class Meta:
        model = Settings
        fields = ("instance_id",)
        extra_kwargs = {
            "instance_id": {"read_only": True},
        }
