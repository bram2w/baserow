from rest_framework import serializers

from baserow.contrib.dashboard.filters.models import DashboardFilter
from baserow.core.formula.serializers import FormulaSerializerField


class DashboardFilterSerializer(serializers.ModelSerializer):
    dashboard_id = serializers.IntegerField(read_only=True)
    formula_name = FormulaSerializerField()
    formula_value = FormulaSerializerField()

    def __init__(self, *args, **kwargs):
        from baserow.contrib.dashboard.application_types import DashboardApplicationType

        kwargs.setdefault("context", {}).setdefault(
            "application_type", DashboardApplicationType
        )
        super().__init__(*args, **kwargs)

    class Meta:
        model = DashboardFilter
        fields = (
            "id",
            "dashboard_id",
            "label",
            "type",
            "mode",
            "multiple",
            "formula_name",
            "formula_value",
        )
        read_only_fields = ("id", "dashboard_id")
