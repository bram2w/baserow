from freezegun import freeze_time

from baserow.contrib.database.fields.periodic_field_update_handler import (
    PeriodicFieldUpdateHandler,
)


def test_get_recently_used_workspace_ids_interval(settings):
    workspace_id = 1
    settings.BASEROW_PERIODIC_FIELD_UPDATE_UNUSED_WORKSPACE_INTERVAL_MIN = 5

    with freeze_time("2020-01-01 12:00"):
        PeriodicFieldUpdateHandler.mark_workspace_as_recently_used(workspace_id)

    # within interval
    with freeze_time("2020-01-01 12:04"):
        result = PeriodicFieldUpdateHandler.get_recently_used_workspace_ids()

        assert result == [workspace_id]

    # outside interval
    with freeze_time("2020-01-01 12:06"):
        result = PeriodicFieldUpdateHandler.get_recently_used_workspace_ids()

        assert result == []


def test_get_recently_used_workspace_ids_multiple_ids(settings):
    workspace_id = 1
    workspace_id_2 = 2
    settings.BASEROW_PERIODIC_FIELD_UPDATE_UNUSED_WORKSPACE_INTERVAL_MIN = 5

    with freeze_time("2020-01-01 00:00"):
        # workspace 1 was used long time ago, outside interval
        PeriodicFieldUpdateHandler.mark_workspace_as_recently_used(workspace_id)

    with freeze_time("2020-01-01 12:00"):
        # workspace 2 was used recently
        PeriodicFieldUpdateHandler.mark_workspace_as_recently_used(workspace_id_2)

        result = PeriodicFieldUpdateHandler.get_recently_used_workspace_ids()
        assert result == [workspace_id_2]

        # workspace 1 has now been used recently too
        PeriodicFieldUpdateHandler.mark_workspace_as_recently_used(workspace_id)
        result = PeriodicFieldUpdateHandler.get_recently_used_workspace_ids()
        assert result == [workspace_id, workspace_id_2]

    # outside interval
    with freeze_time("2020-01-01 12:10"):
        result = PeriodicFieldUpdateHandler.get_recently_used_workspace_ids()
        assert result == []
