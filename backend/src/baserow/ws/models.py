from django.contrib.postgres.indexes import GinIndex
from django.db import models


class RealtimeEvent(models.Model):
    UNLOGGED = True

    id = models.BigAutoField(primary_key=True)
    channel_group = models.TextField()
    payload = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ws_realtime_events"
        indexes = [
            models.Index(
                fields=["channel_group", "id"],
                name="ws_realtime_channel_group_idx",
            ),
            # Recipient containment is queried only on the shared users channel.
            # Page events use the group/id index; indexing their row snapshots
            # adds substantial write amplification without helping replay.
            GinIndex(
                fields=["payload"],
                opclasses=["jsonb_path_ops"],
                condition=models.Q(channel_group="users"),
                name="ws_realtime_users_payload_idx",
            ),
            models.Index(
                fields=["created_at", "id"],
                name="ws_realtime_created_id_idx",
            ),
        ]
