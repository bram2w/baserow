from datetime import datetime, timedelta, timezone

from django.conf import settings

from django_redis import get_redis_connection

RECENTLY_USED_WORKSPACES = "recently_used_workspaces"


def _get_redis_client():
    return get_redis_connection("default")


class PeriodicFieldUpdateHandler:
    """
    Handler to track last row activity
    in workspaces to determine whether a more frequent periodic field
    update is warranted.
    """

    @classmethod
    def mark_workspace_as_recently_used(cls, workspace_id: int):
        """
        Marks a workspace as having a recent row activity.

        :param workspace_id: The workspace that has seen the activity.
        """

        now = datetime.now(tz=timezone.utc)
        rclient = _get_redis_client()
        rclient.zadd(
            RECENTLY_USED_WORKSPACES, {f"{workspace_id}": int(now.timestamp())}, gt=True
        )

    @classmethod
    def get_recently_used_workspace_ids(cls) -> list[int]:
        """
        Returns workspace ids of workspaces that had recent row activity.
        """

        now = datetime.now(tz=timezone.utc)
        threshold = now - timedelta(
            minutes=settings.BASEROW_PERIODIC_FIELD_UPDATE_UNUSED_WORKSPACE_INTERVAL_MIN
        )
        rclient = _get_redis_client()
        rclient.zremrangebyscore(
            RECENTLY_USED_WORKSPACES, 0, int(threshold.timestamp())
        )
        result = rclient.zrange(RECENTLY_USED_WORKSPACES, 0, int(now.timestamp()))
        return [int(workspace_id) for workspace_id in result]
