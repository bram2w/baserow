from django.db import models
from django.db.models import Q

from baserow.contrib.database.fields.models import Field, FileField, SingleSelectField
from baserow.contrib.database.views.models import View
from baserow.core.mixins import HierarchicalModelMixin

OWNERSHIP_TYPE_PERSONAL = "personal"


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


class KanbanViewFieldOptionsManager(models.Manager):
    """
    The View can be trashed and the field options are not deleted, therefore
    we need to filter out the trashed views.
    """

    def get_queryset(self):
        trashed_Q = Q(kanban_view__trashed=True) | Q(field__trashed=True)
        return super().get_queryset().filter(~trashed_Q)


class KanbanViewFieldOptions(HierarchicalModelMixin, models.Model):
    objects = KanbanViewFieldOptionsManager()
    objects_and_trash = models.Manager()

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

    def get_parent(self):
        return self.kanban_view

    class Meta:
        db_table = "database_kanbanviewfieldoptions"
        ordering = (
            "order",
            "field_id",
        )
