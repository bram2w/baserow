from django.conf import settings

from rest_framework import serializers


class GenerateAIFieldValueViewSerializer(serializers.Serializer):
    row_ids = serializers.ListField(
        child=serializers.IntegerField(),
        max_length=settings.BATCH_ROWS_SIZE_LIMIT,
        help_text="The ids of the rows that the values should be generated for.",
    )

    def to_internal_value(self, data):
        return super().to_internal_value(data)
