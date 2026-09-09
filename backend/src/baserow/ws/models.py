from django.contrib.postgres.fields import ArrayField
from django.contrib.postgres.indexes import GinIndex
from django.db import models


class RealtimeEvent(models.Model):
    UNLOGGED = True

    id = models.BigAutoField(primary_key=True)
    channel_group = models.TextField()
    payload = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    # The database derives these from routing metadata, including writes by
    # older workers during a rolling deployment. Replay avoids scanning JSON.
    target_user_ids = ArrayField(
        models.IntegerField(), default=list, db_default=[], editable=False
    )
    all_users = models.BooleanField(default=False, db_default=False, editable=False)

    class Meta:
        db_table = "ws_realtime_events"
        indexes = [
            models.Index(
                fields=["channel_group", "id"],
                name="ws_realtime_channel_group_idx",
            ),
            # Only shared users-channel events need recipient indexes. Page
            # events use group/id, and no full business payload is indexed.
            GinIndex(
                fields=["target_user_ids"],
                condition=models.Q(channel_group="users"),
                name="ws_realtime_targets_idx",
            ),
            models.Index(
                fields=["id"],
                condition=models.Q(channel_group="users", all_users=True),
                name="ws_realtime_all_users_idx",
            ),
            models.Index(
                fields=["created_at", "id"],
                name="ws_realtime_created_id_idx",
            ),
        ]
