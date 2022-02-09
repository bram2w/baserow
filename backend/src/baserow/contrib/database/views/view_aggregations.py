from .registries import ViewAggregationType
from django.db.models import Count

from baserow.contrib.database.fields.registries import field_type_registry

# See official django documentation for list of aggregator:
# https://docs.djangoproject.com/en/4.0/ref/models/querysets/#aggregation-functions


class EmptyCountViewAggregationType(ViewAggregationType):
    """
    The empty count aggregation counts how many values are considered empty for
    the given field.
    """

    type = "empty_count"

    def get_aggregation(self, field_name, model_field, field):
        field_type = field_type_registry.get_by_model(field)
        return Count(
            "id",
            filter=field_type.empty_query(field_name, model_field, field),
        )


class NotEmptyCountViewAggregationType(ViewAggregationType):
    """
    The empty count aggregation counts how many values aren't considered empty for
    the given field.
    """

    type = "not_empty_count"

    def get_aggregation(self, field_name, model_field, field):
        field_type = field_type_registry.get_by_model(field)

        return Count(
            "id",
            filter=~field_type.empty_query(field_name, model_field, field),
        )
