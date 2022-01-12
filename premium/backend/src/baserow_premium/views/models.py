from django.db import models

from baserow.contrib.database.fields.models import Field, FileField, SingleSelectField
from baserow.contrib.database.views.models import View
from baserow.contrib.database.mixins import ParentFieldTrashableModelMixin


class KanbanView(View):
    field_options = models.ManyToManyField(Field, through="KanbanViewFieldOptions")
    single_select_field = models.ForeignKey(
        SingleSelectField,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="kanban_view_single_select_field",
        help_text="The single select field related to the options where rows should "
        "be stacked by.",
    )
    card_cover_image_field = models.ForeignKey(
        FileField,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="kanban_view_card_cover_field",
        help_text="References a file field of which the first image must be shown as "
        "card cover image.",
    )

    class Meta:
        db_table = "database_kanbanview"


class KanbanViewFieldOptions(ParentFieldTrashableModelMixin, models.Model):
    kanban_view = models.ForeignKey(KanbanView, on_delete=models.CASCADE)
    field = models.ForeignKey(Field, on_delete=models.CASCADE)
    hidden = models.BooleanField(
        default=True,
        help_text="Whether or not the field should be hidden in the card.",
    )
    # The default value is the maximum value of the small integer field because a newly
    # created field must always be last.
    order = models.SmallIntegerField(
        default=32767,
        help_text="The order that the field has in the form. Lower value is first.",
    )

    class Meta:
        db_table = "database_kanbanviewfieldoptions"
        ordering = (
            "order",
            "field_id",
        )
