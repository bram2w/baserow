from django.db import models

from baserow.core.mixins import (
    CreatedAndUpdatedOnMixin,
    HierarchicalModelMixin,
    TrashableModelMixin,
)


class DashboardFilter(
    HierarchicalModelMixin, TrashableModelMixin, CreatedAndUpdatedOnMixin, models.Model
):
    """Shared configuration; applied values belong to the visitor's current tab."""

    class Operator(models.TextChoices):
        EQUAL = "equal", "Is"
        NOT_EQUAL = "not_equal", "Is not"
        CONTAINS = "contains", "Contains"
        CONTAINS_NOT = "contains_not", "Does not contain"

    class Mode(models.TextChoices):
        DROPDOWN = "dropdown", "Dropdown"
        INPUT = "input", "Input"

    dashboard = models.ForeignKey(
        "dashboard.Dashboard", on_delete=models.CASCADE, related_name="filters"
    )
    label = models.CharField(max_length=255)
    type = models.CharField(max_length=32, choices=[("text", "Text")], default="text")
    operator = models.CharField(
        max_length=32, choices=Operator.choices, default=Operator.EQUAL
    )
    mode = models.CharField(max_length=32, choices=Mode.choices, default=Mode.DROPDOWN)
    multiple = models.BooleanField(default=False)

    class Meta:
        ordering = ("id",)

    def get_parent(self):
        return self.dashboard
