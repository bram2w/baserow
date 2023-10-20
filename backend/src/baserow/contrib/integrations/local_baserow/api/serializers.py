from rest_framework import serializers

from baserow.contrib.integrations.local_baserow.models import (
    LocalBaserowTableServiceFilter,
)


class LocalBaserowTableServiceFilterSerializer(serializers.ModelSerializer):
    order = serializers.IntegerField(read_only=True)

    class Meta:
        model = LocalBaserowTableServiceFilter
        fields = ("id", "order", "field", "type", "value")
