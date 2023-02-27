import typing

from django.db import models

from baserow.core.mixins import (
    CreatedAndUpdatedOnMixin,
    HierarchicalModelMixin,
    OrderableMixin,
    TrashableModelMixin,
)

if typing.TYPE_CHECKING:
    from baserow.contrib.builder.models import Builder


class Page(
    HierarchicalModelMixin,
    TrashableModelMixin,
    CreatedAndUpdatedOnMixin,
    OrderableMixin,
    models.Model,
):

    builder = models.ForeignKey("builder.Builder", on_delete=models.CASCADE)
    order = models.PositiveIntegerField()
    name = models.CharField(max_length=255)

    class Meta:
        ordering = ("order",)
        unique_together = [["builder", "name"]]

    def get_parent(self):
        return self.builder

    @classmethod
    def get_last_order(cls, builder: "Builder"):
        queryset = Page.objects.filter(builder=builder)
        return cls.get_highest_order_of_queryset(queryset) + 1
