import typing

from django.db import models

from baserow.core.jobs.mixins import (
    JobWithUndoRedoIds,
    JobWithUserIpAddress,
    JobWithWebsocketId,
)
from baserow.core.jobs.models import Job
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


class DuplicatePageJob(
    JobWithUserIpAddress, JobWithWebsocketId, JobWithUndoRedoIds, Job
):

    original_page = models.ForeignKey(
        Page,
        null=True,
        related_name="duplicated_by_jobs",
        on_delete=models.SET_NULL,
        help_text="The baserow page to duplicate.",
    )

    duplicated_page = models.OneToOneField(
        Page,
        null=True,
        related_name="duplicated_from_jobs",
        on_delete=models.SET_NULL,
        help_text="The duplicated Baserow page.",
    )
