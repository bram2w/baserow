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


class DashboardFilterBinding(models.Model):
    """An explicit association, retained as broken if its field is deleted."""

    filter = models.ForeignKey(
        DashboardFilter, on_delete=models.CASCADE, related_name="bindings"
    )
    widget = models.ForeignKey(
        "dashboard.Widget", on_delete=models.CASCADE, related_name="filter_bindings"
    )
    field = models.ForeignKey("database.Field", on_delete=models.SET_NULL, null=True)

    class Meta:
        ordering = ("widget_id",)
        constraints = [
            models.UniqueConstraint(
                fields=("filter", "widget"), name="dashboard_filter_widget_unique"
            )
        ]
