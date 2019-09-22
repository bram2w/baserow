from django.db import models


class OrderableMixin:
    """
    This mixin introduces a set of helpers of the model is orderable by a field.
    """

    @classmethod
    def get_highest_order_of_queryset(cls, queryset, field='order'):
        """

        :param queryset:
        :param field:
        :return:
        """

        return queryset.aggregate(
            models.Max(field)
        ).get(f'{field}__max', 0) or 0
