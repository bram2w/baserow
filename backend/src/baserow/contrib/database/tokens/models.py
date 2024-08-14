from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Q

from baserow.core.mixins import (
    HierarchicalModelMixin,
    ParentWorkspaceTrashableModelMixin,
)
from baserow.core.models import Workspace

User = get_user_model()


class Token(
    HierarchicalModelMixin,
    ParentWorkspaceTrashableModelMixin,
    models.Model,
):
    """
    A token can be used to authenticate a user with the row create, read, update and
    delete endpoints.
    """

    name = models.CharField(
        max_length=100,
        help_text="The human readable name of the database token for the user.",
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
    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        help_text="Only the tables of the workspace can be accessed.",
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

    def get_parent(self):
        return self.workspace


class TokenPermissionManager(models.Manager):
    """
    This manager is needed to avoid problems with tokens of trashed
    but not already deleted databases and tables.
    After 3 days (default) trashed databases and tables are deleted permanently,
    and so are relative token permissions (because of the CASCADE option).
    In the meanwhile, we need to filter out the trashed databases and tables.
    """

    def get_queryset(self):
        trashed_Q = Q(database__trashed=True) | Q(table__trashed=True)
        return super().get_queryset().filter(~trashed_Q)


class TokenPermission(HierarchicalModelMixin, models.Model):
    """
    The existence of a permission indicates that the token has access to a table. If
    neither a database nor table is stored that means that the token has access to all
    tables in the token's group. If a database is provided then it means that the
    token has access to all the tables in the database. If a table is provided then it
    means that the token has access to that table.
    """

    objects = TokenPermissionManager()

    token = models.ForeignKey("database.Token", on_delete=models.CASCADE)
    type = models.CharField(
        max_length=6,
        db_index=True,
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

    def get_parent(self):
        return self.token
