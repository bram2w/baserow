from rest_framework import serializers

from baserow.contrib.dashboard.filters.models import DashboardFilter


class DashboardFilterBindingSerializer(serializers.Serializer):
    table_id = serializers.IntegerField(min_value=1)
    field_id = serializers.IntegerField(min_value=1, allow_null=True)


class DashboardFilterSerializer(serializers.ModelSerializer):
    dashboard_id = serializers.IntegerField(read_only=True)
    bindings = DashboardFilterBindingSerializer(many=True, required=False)

    class Meta:
        model = DashboardFilter
        fields = (
            "id",
            "dashboard_id",
            "label",
            "type",
            "operator",
            "mode",
            "multiple",
            "bindings",
        )
        read_only_fields = ("id", "dashboard_id")
