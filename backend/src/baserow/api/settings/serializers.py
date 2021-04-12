from rest_framework import serializers

from baserow.core.models import Settings


class SettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Settings
        fields = ("allow_new_signups",)
        extra_kwargs = {
            "allow_new_signups": {"required": False},
        }
