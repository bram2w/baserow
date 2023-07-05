from rest_framework import serializers

from baserow.contrib.database.search.handler import ALL_SEARCH_MODES


class SearchQueryParamSerializer(serializers.Serializer):
    search = serializers.CharField(required=False, allow_blank=True, default=None)
    search_mode = serializers.ChoiceField(
        required=False,
        default=None,
        choices=ALL_SEARCH_MODES,
    )
