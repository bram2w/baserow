from django.contrib.auth import get_user_model
from django.db import models

from baserow.core.encoders import JSONEncoderSupportingDataClasses
from baserow.core.mixins import CreatedAndUpdatedOnMixin

User = get_user_model()


class Action(CreatedAndUpdatedOnMixin, models.Model):
    """
    An undoable-action represents a user performed change that can be undone.
    """

    user = models.ForeignKey(User, blank=True, null=True, on_delete=models.SET_NULL)
    workspace = models.ForeignKey(
        "core.Workspace", null=True, on_delete=models.SET_NULL
    )
    session = models.TextField(null=True, blank=True, db_index=True)
    type = models.TextField(db_index=True)
    params = models.JSONField(encoder=JSONEncoderSupportingDataClasses)
    scope = models.TextField(db_index=True)
    undone_at = models.DateTimeField(null=True, blank=True, db_index=True)
    error = models.TextField(null=True, blank=True)
    action_group = models.UUIDField(null=True, blank=True, db_index=True)

    def is_undone(self) -> bool:
        return self.undone_at is not None

    def has_error(self) -> bool:
        return self.error is not None

    def __str__(self) -> str:
        return (
            f"Action(user={self.user_id}, type={self.type}, scope={self.scope}, "
            f"created_on={self.created_on}, updated_on={self.updated_on} "
            f"undone_at={self.undone_at}, params={self.params}, \n"
            f"session={self.session}) action_group={self.action_group}"
        )

    class Meta:
        ordering = ("-created_on",)
        indexes = [
            models.Index(fields=["-created_on", "-id"]),
            models.Index(fields=["-undone_at", "-id"]),
            models.Index(fields=["updated_on", "id"]),
        ]
