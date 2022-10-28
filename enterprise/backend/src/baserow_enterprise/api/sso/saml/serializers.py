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
