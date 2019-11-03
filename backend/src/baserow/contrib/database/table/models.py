from django.db import models

from baserow.core.mixins import OrderableMixin


class Table(OrderableMixin, models.Model):
    database = models.ForeignKey('database.Database', on_delete=models.CASCADE)
    order = models.PositiveIntegerField()
    name = models.CharField(max_length=255)

    class Meta:
        ordering = ('order',)

    @classmethod
    def get_last_order(cls, database):
        queryset = Table.objects.filter(database=database)
        return cls.get_highest_order_of_queryset(queryset) + 1
