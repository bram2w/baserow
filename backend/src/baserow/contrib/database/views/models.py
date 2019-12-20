from django.db import models
from django.contrib.contenttypes.models import ContentType

from baserow.core.mixins import OrderableMixin, PolymorphicContentTypeMixin


def get_default_view_content_type():
    return ContentType.objects.get_for_model(View)


class View(OrderableMixin, PolymorphicContentTypeMixin, models.Model):
    table = models.ForeignKey('database.Table', on_delete=models.CASCADE)
    order = models.PositiveIntegerField()
    name = models.CharField(max_length=255)
    content_type = models.ForeignKey(
        ContentType,
        verbose_name='content type',
        related_name='database_views',
        on_delete=models.SET(get_default_view_content_type)
    )

    class Meta:
        ordering = ('order',)

    @classmethod
    def get_last_order(cls, table):
        queryset = View.objects.filter(table=table)
        return cls.get_highest_order_of_queryset(queryset) + 1


class GridView(View):
    pass
