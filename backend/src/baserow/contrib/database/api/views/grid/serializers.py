from rest_framework import serializers

from baserow.contrib.database.views.models import GridViewFieldOptions


class GridViewFieldOptionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = GridViewFieldOptions
        fields = ("width", "hidden", "order")


class GridViewFilterSerializer(serializers.Serializer):
    field_ids = serializers.ListField(
        allow_empty=False,
        required=False,
        default=None,
        child=serializers.IntegerField(),
        help_text="Only the fields related to the provided ids are added to the "
        "response. If None are provided all fields will be returned.",
    )
    row_ids = serializers.ListField(
        allow_empty=False,
        child=serializers.IntegerField(),
        help_text="Only rows related to the provided ids are added to the response.",
    )
