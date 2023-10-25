from rest_framework import serializers

from baserow.contrib.integrations.local_baserow.models import (
    LocalBaserowTableServiceFilter,
    LocalBaserowTableServiceSort,
)


class LocalBaserowTableServiceSortSerializer(serializers.ModelSerializer):
    order = serializers.IntegerField(read_only=True)

    class Meta:
        model = LocalBaserowTableServiceSort
        fields = ("id", "field", "order", "order_by")


class LocalBaserowTableServiceFilterSerializer(serializers.ModelSerializer):
    order = serializers.IntegerField(read_only=True)

    class Meta:
        model = LocalBaserowTableServiceFilter
        fields = ("id", "order", "field", "type", "value")
