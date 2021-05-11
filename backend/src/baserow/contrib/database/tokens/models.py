from django.db import models
from django.contrib.auth import get_user_model

from baserow.core.models import Group


User = get_user_model()


class Token(models.Model):
    """
    A token can be used to authenticate a user with the row create, read, update and
    delete endpoints.
    """

    name = models.CharField(
        max_length=100, help_text="The human readable name of the token for the user."
    )
    key = models.CharField(
        max_length=32,
        unique=True,
        db_index=True,
        help_text="The unique token key that can be used to authorize for the table "
        "row endpoints.",
    )
    created = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, help_text="The user that owns the token."
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        help_text="Only the tables of the group can be accessed.",
    )
    handled_calls = models.PositiveIntegerField(
        default=0,
        help_text="Indicates the total amount of calls were handled using this token.",
    )
    last_call = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Timestamp when the last call was handled using this token.",
    )

    class Meta:
        ordering = ("id",)


class TokenPermission(models.Model):
    """
    The existence of a permission indicates that the token has access to a table. If
    neither a database nor table is stored that means that the token has access to all
    tables in the token's group. If a database is provided then it means that the
    token has access to all the tables in the database. If a table is provided then it
    means that the token has access to that table.
    """

    token = models.ForeignKey("database.Token", on_delete=models.CASCADE)
    type = models.CharField(
        max_length=6,
        choices=(
            ("create", "Create"),
            ("read", "Read"),
            ("update", "Update"),
            ("delete", "Delete"),
        ),
    )
    database = models.ForeignKey(
        "database.Database", on_delete=models.CASCADE, blank=True, null=True
    )
    table = models.ForeignKey(
        "database.Table", on_delete=models.CASCADE, blank=True, null=True
    )
