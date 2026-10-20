from rest_framework import serializers

from baserow.contrib.dashboard.filters.models import DashboardFilter
from baserow.core.formula.serializers import FormulaSerializerField


class DashboardFilterOptionSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255, trim_whitespace=False)
    value = serializers.CharField(trim_whitespace=False)


class DashboardFilterSerializer(serializers.ModelSerializer):
    dashboard_id = serializers.IntegerField(read_only=True)
    options = DashboardFilterOptionSerializer(many=True, required=False)
    formula_name = FormulaSerializerField()
    formula_value = FormulaSerializerField()

    def __init__(self, *args, **kwargs):
        from baserow.contrib.dashboard.application_types import DashboardApplicationType

        kwargs.setdefault("context", {}).setdefault(
            "application_type", DashboardApplicationType
        )
        super().__init__(*args, **kwargs)

    def validate_options(self, options):
        values = [option["value"] for option in options]
        if len(set(values)) != len(values):
            raise serializers.ValidationError("Each option must have a unique value.")
        if any(not value.strip() for value in values):
            raise serializers.ValidationError("Option values cannot be blank.")
        return options

    class Meta:
        model = DashboardFilter
        fields = (
            "id",
            "dashboard_id",
            "label",
            "type",
            "mode",
            "multiple",
            "option_type",
            "options",
            "formula_name",
            "formula_value",
        )
        read_only_fields = ("id", "dashboard_id")
