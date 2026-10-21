from django.db import models

from baserow.contrib.database.search.models import AbstractPendingSearchDataUpdate


class SemanticSearchField(models.Model):
    """
    Exists for every field that has semantic search enabled. Deleting it disables
    semantic search for the field.
    """

    class Status(models.TextChoices):
        INDEXING = "indexing"
        READY = "ready"
        ERROR = "error"

    field = models.OneToOneField(
        "database.Field",
        on_delete=models.CASCADE,
        related_name="semantic_search",
    )
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.INDEXING,
    )


class SemanticSearchPendingUpdate(AbstractPendingSearchDataUpdate):
    copy_vectors_from_field_id = models.PositiveIntegerField(
        null=True,
        help_text="A field with the same rows of which the vectors are copied before "
        "an update of all rows, so that unchanged values aren't embedded again.",
    )
    processed_until_row_id = models.PositiveIntegerField(
        null=True,
        help_text="Allows an update of all rows to continue where it stopped.",
    )
