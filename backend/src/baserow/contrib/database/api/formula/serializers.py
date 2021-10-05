from rest_framework import serializers

from baserow.contrib.database.fields.field_types import FormulaFieldType
from baserow.contrib.database.fields.models import FormulaField


class TypeFormulaRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = FormulaField
        fields = ("formula",)


class TypeFormulaResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = FormulaField
        fields = FormulaFieldType.serializer_field_names
