from typing import Dict
from urllib.parse import urlparse

from rest_framework import serializers

from baserow.api.user.serializers import NormalizedEmailField


class SamlLoginRequestSerializer(serializers.Serializer):
    email = NormalizedEmailField(required=False)
    original = serializers.CharField(required=False)
    language = serializers.CharField(required=False)
    template = serializers.CharField(required=False)

    def validate_original(self, value):
        """Only relative URLs are allowed."""

        if urlparse(value).hostname is not None:
            return None
        return value

    def to_representation(self, instance) -> Dict[str, str]:
        data = super().to_representation(instance)
        return {k: v for k, v in data.items() if v is not None}
