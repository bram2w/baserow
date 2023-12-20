from rest_framework import serializers

from baserow.contrib.integrations.local_baserow.models import (
    LocalBaserowTableServiceFilter,
    LocalBaserowTableServiceSort,
)
from baserow.core.formula.serializers import FormulaSerializerField


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


class LocalBaserowTableServiceFieldMappingSerializer(serializers.Serializer):
    field_id = serializers.IntegerField(
        help_text="The primary key of the associated database table field."
    )
    value = FormulaSerializerField(allow_blank=True)
