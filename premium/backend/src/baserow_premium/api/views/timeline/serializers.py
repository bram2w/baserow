from baserow_premium.views.models import TimelineViewFieldOptions
from rest_framework import serializers


class TimelineViewFieldOptionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = TimelineViewFieldOptions
        fields = (
            "hidden",
            "order",
        )
