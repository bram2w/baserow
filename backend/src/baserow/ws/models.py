from django.contrib.postgres.fields import ArrayField
from django.contrib.postgres.indexes import GinIndex
from django.db import models


class RealtimeEvent(models.Model):
    UNLOGGED = True

    id = models.BigAutoField(primary_key=True)
    channel_group = models.TextField()
    payload = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    # PostgreSQL trigger ws_realtime_event_targets_before_write populates these
    # from payload on INSERT or updates to payload/channel_group. It calls
    # ws_set_realtime_event_targets() from migrations/0002_realtime_event_indexes.py,
    # including for older workers during a rolling deployment, so replay can use
    # recipient indexes instead of scanning JSON.
    target_user_ids = ArrayField(
        models.IntegerField(), default=list, db_default=[], editable=False
    )
    all_users = models.BooleanField(default=False, db_default=False, editable=False)
    # Set only when cleanup retains this original as expired routing evidence.
    sentinel_key = models.BinaryField(null=True, db_default=None)

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
        constraints = [
            models.UniqueConstraint(
                fields=["sentinel_key"],
                condition=models.Q(sentinel_key__isnull=False),
                name="ws_realtime_sentinel_key_uniq",
            )
        ]


class RealtimeEventHistoryState(models.Model):
    """Cursors below this floor can cross history that is no longer known."""

    UNLOGGED = True

    id = models.PositiveSmallIntegerField(primary_key=True, db_default=1)
    floor = models.BigIntegerField(db_default=0)

    class Meta:
        db_table = "ws_realtime_event_history_state"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(id=1), name="ws_history_state_singleton"
            )
        ]
