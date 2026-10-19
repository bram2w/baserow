from rest_framework import serializers

from baserow.contrib.dashboard.filters.models import DashboardFilter


class DashboardFilterSerializer(serializers.ModelSerializer):
    dashboard_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = DashboardFilter
        fields = ("id", "dashboard_id", "label", "type", "operator", "mode", "multiple")
        read_only_fields = ("id", "dashboard_id")
