from rest_framework import serializers

from baserow.contrib.integrations.local_baserow.models import (
    LocalBaserowTableServiceFilter,
    LocalBaserowTableServiceSort,
)
from baserow.core.formula.serializers import (
    FormulaSerializerField,
    OptionalFormulaSerializerField,
)


class LocalBaserowTableServiceSortSerializer(serializers.ModelSerializer):
    order = serializers.IntegerField(read_only=True)

    class Meta:
        model = LocalBaserowTableServiceSort
        fields = ("id", "field", "order", "order_by")


class LocalBaserowTableServiceFilterSerializer(serializers.ModelSerializer):
    value = OptionalFormulaSerializerField(
        allow_blank=True,
        help_text="A formula for the filter's value.",
        is_formula_field_name="value_is_formula",
    )
    value_is_formula = serializers.BooleanField(
        default=False, help_text="Indicates whether the value is a formula or not."
    )
    order = serializers.IntegerField(read_only=True)

    class Meta:
        model = LocalBaserowTableServiceFilter
        fields = ("id", "order", "field", "type", "value", "value_is_formula")


class LocalBaserowTableServiceFieldMappingSerializer(serializers.Serializer):
    field_id = serializers.IntegerField(
        help_text="The primary key of the associated database table field."
    )
    enabled = serializers.BooleanField(
        help_text="Indicates whether the field mapping is enabled or not."
    )
    value = FormulaSerializerField(allow_blank=True)
