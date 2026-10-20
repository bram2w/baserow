from django.db import models

from baserow.core.formula.field import FormulaField
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

    class OptionType(models.TextChoices):
        MANUAL = "manual", "Manual"
        FORMULAS = "formulas", "Data source"

    dashboard = models.ForeignKey(
        "dashboard.Dashboard", on_delete=models.CASCADE, related_name="filters"
    )
    label = models.CharField(max_length=255)
    type = models.CharField(max_length=32, choices=[("text", "Text")], default="text")
    # TODO ZDM: remove this unused field in the next version.
    operator = models.CharField(
        max_length=32, choices=Operator.choices, default=Operator.EQUAL
    )
    mode = models.CharField(max_length=32, choices=Mode.choices, default=Mode.DROPDOWN)
    multiple = models.BooleanField(default=False)
    # TODO ZDM: remove these unused manual-option fields in the next version.
    option_type = models.CharField(
        max_length=32,
        choices=OptionType.choices,
        default=OptionType.MANUAL,
        db_default=OptionType.MANUAL,
    )
    options = models.JSONField(default=list, db_default=[])
    formula_name = FormulaField(db_default="")
    formula_value = FormulaField(db_default="")

    class Meta:
        ordering = ("id",)

    def get_parent(self):
        return self.dashboard


class DashboardFilterBinding(models.Model):
    """Legacy configuration retained while upgrading existing dashboards."""

    # TODO ZDM: remove this unused model in the next version.

    filter = models.ForeignKey(
        DashboardFilter, on_delete=models.CASCADE, related_name="bindings"
    )
    table = models.ForeignKey("database.Table", on_delete=models.CASCADE)
    field = models.ForeignKey("database.Field", on_delete=models.SET_NULL, null=True)

    class Meta:
        ordering = ("table_id",)
        constraints = [
            models.UniqueConstraint(
                fields=("filter", "table"), name="dashboard_filter_table_unique"
            )
        ]
