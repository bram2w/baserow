import dataclasses
import json

from datetime import datetime, date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class JSONEncoderSupportingDataClasses(json.JSONEncoder):
    def default(self, o):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        if isinstance(o, Decimal):
            return str(o)
        if isinstance(o, (datetime, date)):
            return str(o)
        return super().default(o)


class Action(models.Model):
    """
    An action represents a user performed change to Baserow.
    """

    user = models.ForeignKey(User, blank=True, null=True, on_delete=models.SET_NULL)
    session = models.TextField(null=True, blank=True, db_index=True)
    created_on = models.DateTimeField(auto_now_add=True, db_index=True)
    type = models.TextField()
    params = models.JSONField(encoder=JSONEncoderSupportingDataClasses)
    scope = models.TextField(db_index=True)
    undone_at = models.DateTimeField(null=True, blank=True, db_index=True)
    error = models.TextField(null=True, blank=True)

    def is_undone(self):
        return self.undone_at is not None

    def has_error(self):
        return self.error is not None

    def __str__(self):
        return (
            f"Action(user={self.user_id}, type={self.type}, scope={self.scope}, "
            f"created_on={self.created_on},  undone_at={self.undone_at}, params="
            f"{self.params}, \nsession={self.session})"
        )

    class Meta:
        ordering = ("-created_on",)
        indexes = [
            models.Index(fields=["-created_on", "-id"]),
            models.Index(fields=["-undone_at", "-id"]),
        ]
