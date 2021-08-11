from django.contrib.auth import get_user_model
from django.db import models

from baserow.contrib.database.table.models import Table
from baserow.core.mixins import CreatedAndUpdatedOnMixin

User = get_user_model()


class RowComment(CreatedAndUpdatedOnMixin, models.Model):
    """
    A user made comment on a specific row in a user table in Baserow.
    """

    table = models.ForeignKey(
        Table,
        on_delete=models.CASCADE,
        help_text="The table the row this comment is for is found in. ",
    )
    row_id = models.PositiveIntegerField(
        help_text="The id of the row the comment is for."
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, help_text="The user who made the comment."
    )
    comment = models.TextField(help_text="The users comment.")

    class Meta:
        db_table = "database_rowcomment"
        ordering = ("-created_on",)
        indexes = [models.Index(fields=["table", "row_id", "-created_on"])]
