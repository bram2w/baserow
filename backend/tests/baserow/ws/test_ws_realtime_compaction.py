import os
from contextlib import closing
from datetime import timedelta
from unittest.mock import MagicMock

from django.db import OperationalError, connection, transaction
from django.utils import timezone

import pytest
from asgiref.sync import sync_to_async
from channels.testing import WebsocketCommunicator

from baserow.config.asgi import application
from baserow.ws import realtime_events
from baserow.ws import replay as replay_module
from baserow.ws.models import (
    RealtimeEvent,
    RealtimeEventHistoryState,
)
from baserow.ws.realtime_events import (
    FIRST_CONNECT_CURSOR,
    NO_REPLAY_AVAILABLE,
    RealtimeEventHandler,
)

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.websockets]


@pytest.fixture(autouse=True)
def known_history(settings):
    settings.BASEROW_REALTIME_REPLAY_MAX_EVENTS = 100
    RealtimeEventHistoryState.objects.update_or_create(pk=1, defaults={"floor": 0})


def group_event(*, event_type="rows_updated", own=None, excluded=None, **data):
    event = {
        "type": "broadcast_to_group",
        "payload": {"type": event_type, **data},
        "ignore_web_socket_id": own,
    }
    if excluded is not None:
        event["exclude_user_ids"] = excluded
    return event


def users_event(*, recipients=None, everyone=False, own=None):
    return {
        "type": "broadcast_to_users",
        "payload": {"type": "workspace_updated", "private_data": "omit-me"},
        "user_ids": [42] if recipients is None else recipients,
        "send_to_all_users": everyone,
        "ignore_web_socket_id": own,
    }


def individual_event(*, recipients=None, own=None):
    return {
        "type": "broadcast_to_users_individual_payloads",
        "payload_map": {
            str(user_id): {"type": event_type, "private_data": "omit-me"}
            for user_id, event_type in (
                {42: "workspace_updated"} if recipients is None else recipients
            ).items()
        },
        "ignore_web_socket_id": own,
    }


def record(group="table-1", payload=None, *, age=timedelta(), now=None):
    event_id = RealtimeEventHandler.record_events(
        [(group, group_event() if payload is None else payload)]
    )[0]
    RealtimeEvent.objects.filter(pk=event_id).update(
        created_at=(timezone.now() if now is None else now) - age
    )
    return event_id


def replay(cursor, *, user=42, groups=None, socket="own", history_refresh=False):
    return RealtimeEventHandler.get_replay_events_result(
        user,
        ["table-1"] if groups is None else groups,
        cursor,
        socket,
        supports_row_history_refresh=history_refresh,
    )


def cleanup():
    return RealtimeEventHandler.cleanup_old_realtime_events(timedelta(days=1))


def delete_with_old_worker_sql(event_ids):
    # An older Celery worker knows only the existing full-event table.
    with connection.cursor() as cursor:
        cursor.execute("DELETE FROM ws_realtime_events WHERE id = ANY(%s)", [event_ids])


def test_compacted_irrelevant_history_allows_recent_relevant_replay():
    baseline = record("table-other", age=timedelta(days=3))
    irrelevant = record("table-other", age=timedelta(days=2))
    recent = record(age=timedelta(hours=1))

    cleanup()

    assert not RealtimeEvent.objects.filter(pk=baseline).exists()
    assert RealtimeEvent.objects.filter(pk=irrelevant).exists()
    result = replay(baseline)
    assert result.force_refresh is False
    assert [event.id for event in result.replay_events] == [recent]
    assert result.latest_event_id >= recent


@pytest.mark.parametrize(
    "group,payload,relevant",
    [
        ("table-1", group_event(), True),
        ("table-other", group_event(), False),
        ("table-1", group_event(own="own"), False),
        ("table-1", group_event(own="other"), True),
        ("table-1", group_event(excluded=[42]), False),
        ("table-1", group_event(excluded=[7]), True),
        ("users", users_event(), True),
        ("users", users_event(recipients=[7]), False),
        ("users", users_event(recipients=[], everyone=True), True),
        ("users", users_event(own="own"), False),
        ("users", individual_event(), True),
        ("users", individual_event(recipients={7: "workspace_updated"}), False),
        ("users", individual_event(own="own"), False),
    ],
    ids=[
        "page",
        "other-page",
        "own-page",
        "other-socket-page",
        "excluded-page",
        "other-excluded-page",
        "target-user",
        "other-user",
        "everyone",
        "own-user",
        "individual",
        "other-individual",
        "own-individual",
    ],
)
def test_expired_payload_and_retained_original_have_identical_routing(
    group, payload, relevant
):
    baseline = record("baseline", age=timedelta(days=3))
    event_id = record(group, payload, age=timedelta(days=2))

    # Payload time acceptance must not depend on whether Celery ran on time.
    assert replay(baseline).force_refresh is relevant
    cleanup()
    assert RealtimeEvent.objects.filter(pk=event_id).exists()
    result = replay(baseline)
    assert result.force_refresh is relevant
    assert result.replay_events == []


def test_compaction_keeps_the_latest_original_event_for_the_same_route():
    first = record(payload=group_event(value="old-secret"), age=timedelta(days=3))
    second = record(payload=group_event(value="new-secret"), age=timedelta(days=2))
    original = RealtimeEvent.objects.get(pk=second)
    cleanup()

    retained = RealtimeEvent.objects.get()
    assert retained.id == second
    assert retained.channel_group == original.channel_group
    assert retained.payload == original.payload
    assert retained.created_at == original.created_at
    assert RealtimeEventHistoryState.objects.get(pk=1).floor == 0
    assert replay(first).force_refresh is True
    assert replay(second).force_refresh is False


@pytest.mark.parametrize("event_kind", ["page", "users", "individual"])
def test_absent_own_socket_key_keeps_full_and_compacted_routing_equivalent(event_kind):
    baseline = record("baseline", age=timedelta(days=3))
    payload = {
        "page": group_event(),
        "users": users_event(),
        "individual": individual_event(),
    }[event_kind]
    del payload["ignore_web_socket_id"]
    event_id = record(
        "table-1" if event_kind == "page" else "users",
        payload,
        age=timedelta(days=2),
    )
    assert replay(baseline).force_refresh is True
    cleanup()
    assert RealtimeEvent.objects.filter(pk=event_id).exists()
    assert replay(baseline).force_refresh is True


def test_compaction_keeps_own_socket_and_exclusion_audiences_distinct():
    ids = [
        record(payload=group_event(own="own"), age=timedelta(days=2)),
        record(payload=group_event(own="other"), age=timedelta(days=2)),
        record(payload=group_event(excluded=[42]), age=timedelta(days=2)),
        record(payload=group_event(excluded=[7]), age=timedelta(days=2)),
    ]
    cleanup()
    assert set(RealtimeEvent.objects.values_list("id", flat=True)) == set(ids)


@pytest.mark.parametrize("individual", [False, True], ids=["group", "individual"])
def test_compaction_keeps_distinct_inner_event_types(individual):
    for event_type in ("rows_updated", "rows_deleted"):
        record(
            "users" if individual else "table-1",
            payload=(
                individual_event(recipients={42: event_type, 7: "workspace_updated"})
                if individual
                else group_event(event_type=event_type)
            ),
            age=timedelta(days=2),
        )
    originals = list(
        RealtimeEvent.objects.order_by("id").values("id", "payload", "created_at")
    )

    assert cleanup() == 0

    assert (
        list(RealtimeEvent.objects.order_by("id").values("id", "payload", "created_at"))
        == originals
    )
    keys = list(RealtimeEvent.objects.values_list("sentinel_key", flat=True))
    assert all(key is not None for key in keys)
    assert len(set(keys)) == 2


def test_distinct_oldest_routes_do_not_starve_later_duplicate_cleanup(monkeypatch):
    monkeypatch.setattr(realtime_events, "REALTIME_EVENTS_CLEANUP_BATCH_SIZE", 2)
    unique = [record(f"unique-{index}", age=timedelta(days=3)) for index in range(6)]
    first = record("repeated", age=timedelta(days=2))
    latest = record("repeated", age=timedelta(hours=36))

    assert cleanup() == 1

    assert set(RealtimeEvent.objects.values_list("id", flat=True)) == {
        *unique,
        latest,
    }
    assert not RealtimeEvent.objects.filter(pk=first).exists()
    assert RealtimeEventHistoryState.objects.get(pk=1).floor == 0
    assert cleanup() == 0


def test_same_route_spanning_batches_keeps_one_exact_original(monkeypatch):
    monkeypatch.setattr(realtime_events, "REALTIME_EVENTS_CLEANUP_BATCH_SIZE", 2)
    ids = [
        record(payload=group_event(value=index), age=timedelta(days=2))
        for index in range(7)
    ]
    original = RealtimeEvent.objects.get(pk=ids[-1])

    assert cleanup() == 6

    retained = RealtimeEvent.objects.get()
    assert retained.id == original.id
    assert retained.payload == original.payload
    assert retained.created_at == original.created_at
    assert RealtimeEventHistoryState.objects.get(pk=1).floor == 0


def test_retention_increase_still_uses_newer_sentinel_as_replacement(settings):
    settings.REALTIME_REPLAY_RETENTION_HOURS = 24
    first = record(payload=group_event(value="lower-id"), age=timedelta(hours=1))
    latest = record(payload=group_event(value="highest-id"), age=timedelta(days=2))
    cleanup()
    original = RealtimeEvent.objects.get(pk=latest)
    settings.REALTIME_REPLAY_RETENTION_HOURS = 240
    RealtimeEvent.objects.filter(pk=first).update(
        created_at=timezone.now() - timedelta(days=11)
    )

    assert (
        RealtimeEventHandler.cleanup_old_realtime_events(
            RealtimeEventHandler.get_replay_retention()
        )
        == 1
    )

    retained = RealtimeEvent.objects.get()
    assert retained.id == latest
    assert retained.payload == original.payload
    assert retained.created_at == original.created_at
    assert RealtimeEventHistoryState.objects.get(pk=1).floor == 0


def test_failed_sentinel_promotion_rolls_back_markers_and_originals():
    ids = [
        record(payload=group_event(value=index), age=timedelta(days=2))
        for index in range(2)
    ]

    def fail_after_promotion(execute, sql, params, many, context):
        result = execute(sql, params, many, context)
        if sql.startswith("UPDATE ws_realtime_events") and "promoted" in sql:
            raise OperationalError("Failure after sentinel promotion")
        return result

    with (
        connection.execute_wrapper(fail_after_promotion),
        pytest.raises(OperationalError),
    ):
        cleanup()

    assert (
        list(RealtimeEvent.objects.order_by("id").values_list("id", flat=True)) == ids
    )
    assert not RealtimeEvent.objects.filter(sentinel_key__isnull=False).exists()
    assert RealtimeEventHistoryState.objects.get(pk=1).floor == 0


@pytest.mark.parametrize("stage", ["promotion", "deletion"])
def test_compaction_deadline_rolls_back_completed_writes(monkeypatch, stage):
    ids = [
        record(payload=group_event(value=index), age=timedelta(days=2))
        for index in range(2)
    ]
    now = 0
    deadline = realtime_events.REALTIME_EVENTS_CLEANUP_BUDGET_SECONDS
    monkeypatch.setattr(realtime_events, "monotonic", lambda: now)

    def exhaust_budget_after_write(execute, sql, params, many, context):
        nonlocal now
        result = execute(sql, params, many, context)
        if (
            stage == "promotion"
            and sql.startswith("UPDATE ws_realtime_events")
            and "promoted" in sql
        ) or (
            stage == "deletion"
            and sql.startswith("DELETE FROM ws_realtime_events WHERE id = ANY")
        ):
            now = deadline + 1
        return result

    with connection.execute_wrapper(exhaust_budget_after_write):
        result = RealtimeEventHandler._compact_realtime_events_batch(
            timezone.now() - timedelta(days=1), deadline
        )

    assert now > deadline, "The selected write must finish before budget exhaustion"
    assert result == (0, 0)
    assert (
        list(RealtimeEvent.objects.order_by("id").values_list("id", flat=True)) == ids
    )
    assert not RealtimeEvent.objects.filter(sentinel_key__isnull=False).exists()
    assert RealtimeEventHistoryState.objects.get(pk=1).floor == 0
    with connection.cursor() as cursor:
        cursor.execute("SELECT current_setting('baserow.realtime_compacting', true)")
        assert cursor.fetchone()[0] != "on"


def test_compaction_does_not_disable_loss_tracking_for_later_legacy_deletes():
    first = record(age=timedelta(days=3))
    latest = record(age=timedelta(days=2))
    assert cleanup() == 1
    assert not RealtimeEvent.objects.filter(pk=first).exists()
    assert RealtimeEventHistoryState.objects.get(pk=1).floor == 0
    with connection.cursor() as cursor:
        cursor.execute("SELECT current_setting('baserow.realtime_compacting', true)")
        assert cursor.fetchone()[0] != "on"

    delete_with_old_worker_sql([latest])

    assert RealtimeEventHistoryState.objects.get(pk=1).floor == latest
    assert replay(first).force_refresh is True


def test_expired_original_payload_is_not_returned_by_the_replay_query():
    baseline = record("baseline", age=timedelta(days=3))
    expired = record(
        payload=group_event(secret="large-private-data"), age=timedelta(days=2)
    )
    cleanup()

    rows = RealtimeEventHandler._get_replay_snapshot(42, ["table-1"], baseline, "own")

    assert len(rows) == 1
    assert rows[0][2] == expired
    assert rows[0][4] is None
    assert RealtimeEvent.objects.get(pk=expired).payload["payload"]["secret"] == (
        "large-private-data"
    )


def test_legacy_delete_advances_the_loss_floor_atomically():
    event_id = record(payload=group_event(value="private"))
    with pytest.raises(RuntimeError, match="rollback"):
        with transaction.atomic():
            delete_with_old_worker_sql([event_id])
            assert not RealtimeEvent.objects.filter(pk=event_id).exists()
            assert RealtimeEventHistoryState.objects.get(pk=1).floor == event_id
            raise RuntimeError("rollback")

    assert RealtimeEvent.objects.filter(pk=event_id).exists()
    assert RealtimeEventHistoryState.objects.get(pk=1).floor == 0
    delete_with_old_worker_sql([event_id])
    assert RealtimeEventHistoryState.objects.get(pk=1).floor == event_id


@pytest.mark.parametrize("microseconds,replayable", [(0, True), (1, False)])
@pytest.mark.parametrize("retention_hours", [1, 24, 48, 240])
def test_payload_age_cutoff_is_enforced_without_cleanup(
    settings, monkeypatch, microseconds, replayable, retention_hours
):
    settings.REALTIME_REPLAY_RETENTION_HOURS = retention_hours
    now = timezone.now()
    monkeypatch.setattr(realtime_events.timezone, "now", lambda: now)
    baseline = record("baseline", age=timedelta(hours=retention_hours + 1), now=now)
    event_id = record(
        age=timedelta(hours=retention_hours, microseconds=microseconds), now=now
    )
    result = replay(baseline)
    assert result.force_refresh is not replayable
    assert [event.id for event in result.replay_events] == (
        [event_id] if replayable else []
    )
    assert RealtimeEvent.objects.filter(pk=event_id).exists()


def test_increasing_retention_cannot_replay_a_previous_sentinel(settings):
    settings.REALTIME_REPLAY_RETENTION_HOURS = 24
    baseline = record("baseline", age=timedelta(days=4))
    removed = record(payload=group_event(value="missing"), age=timedelta(days=3))
    retained = record(payload=group_event(value="retained"), age=timedelta(days=2))
    cleanup()
    assert not RealtimeEvent.objects.filter(pk=removed).exists()
    assert RealtimeEvent.objects.get(pk=retained).sentinel_key is not None

    settings.REALTIME_REPLAY_RETENTION_HOURS = 240
    result = replay(baseline)

    assert result.force_refresh is True
    assert result.refresh_reason == "expired_payload"
    assert result.replay_events == []
    rows = RealtimeEventHandler._get_replay_snapshot(42, ["table-1"], baseline, "own")
    assert rows[0][2] == retained
    assert rows[0][4] is None


@pytest.mark.parametrize("retention_hours", [1, 48, 240])
def test_cleanup_preserves_the_configured_full_retention_boundary(
    settings, monkeypatch, retention_hours
):
    from baserow.ws.tasks import cleanup_old_realtime_events

    settings.REALTIME_REPLAY_RETENTION_HOURS = retention_hours
    now = timezone.now()
    monkeypatch.setattr(realtime_events.timezone, "now", lambda: now)
    baseline = record(
        "baseline", age=timedelta(hours=retention_hours, microseconds=1), now=now
    )
    boundary = record(age=timedelta(hours=retention_hours), now=now)
    fresh = record(
        age=timedelta(hours=retention_hours) - timedelta(microseconds=1), now=now
    )

    cleanup_old_realtime_events()

    assert list(
        RealtimeEvent.objects.filter(pk__in=[boundary, fresh])
        .order_by("id")
        .values_list("id", "sentinel_key")
    ) == [(boundary, None), (fresh, None)]
    result = replay(baseline)
    assert result.force_refresh is False
    assert [event.id for event in result.replay_events] == [boundary, fresh]


@pytest.mark.parametrize("compacted", [False, True])
@pytest.mark.parametrize("supports_refresh", [False, True])
@pytest.mark.parametrize("channel", ["page", "users"])
def test_row_history_is_ignored_only_for_clients_that_refetch_it(
    compacted, supports_refresh, channel
):
    baseline = record("baseline", age=timedelta(days=3))
    payload = group_event(event_type="row_history_updated")
    if channel == "users":
        payload = users_event()
        payload["payload"]["type"] = "row_history_updated"
    event_id = record(
        "users" if channel == "users" else "table-1",
        payload=payload,
        age=timedelta(days=2),
    )
    if compacted:
        cleanup()
        assert RealtimeEvent.objects.filter(pk=event_id).exists()
    result = replay(baseline, history_refresh=supports_refresh)
    assert result.force_refresh is not supports_refresh
    assert result.replay_events == []


@pytest.mark.parametrize("compacted", [False, True])
def test_individual_row_history_filter_uses_the_current_recipients_payload(compacted):
    baseline = record("baseline", age=timedelta(days=3))
    event_id = record(
        "users",
        individual_event(
            recipients={42: "row_history_updated", 7: "workspace_updated"}
        ),
        age=timedelta(days=2),
    )
    if compacted:
        original = RealtimeEvent.objects.get(pk=event_id).payload
        cleanup()
        assert RealtimeEvent.objects.get(pk=event_id).payload == original
    assert replay(baseline, user=42, history_refresh=True).force_refresh is False
    assert replay(baseline, user=7, history_refresh=True).force_refresh is True


def test_known_empty_history_accepts_zero_cursor():
    result = replay(0)
    assert result.force_refresh is False
    assert result.latest_event_id == 0
    assert result.replay_events == []


def test_cursor_below_history_floor_is_rejected_even_when_baseline_exists():
    baseline = record("baseline")
    latest = record("other")
    RealtimeEventHistoryState.objects.filter(pk=1).update(floor=latest)
    assert replay(baseline).force_refresh is True
    assert replay(latest).force_refresh is False
    assert replay(FIRST_CONNECT_CURSOR).latest_event_id == latest


def test_cursor_above_known_history_is_rejected():
    latest = record("other")
    assert replay(latest + 1000).force_refresh is True


def test_missing_history_state_reestablishes_a_conservative_floor():
    baseline = record("baseline")
    latest = record("other")
    RealtimeEventHistoryState.objects.all().delete()
    assert replay(baseline).force_refresh is True
    state = RealtimeEventHistoryState.objects.get(pk=1)
    assert state.floor >= latest
    assert replay(FIRST_CONNECT_CURSOR).latest_event_id >= state.floor


def test_first_connect_includes_compacted_history_high_water_mark():
    event_id = record("other")
    delete_with_old_worker_sql([event_id])
    result = replay(FIRST_CONNECT_CURSOR)
    assert result.force_refresh is False
    assert result.latest_event_id == event_id


def test_legacy_delete_advances_floor_past_a_locked_surviving_baseline():
    baseline = record("baseline", age=timedelta(days=9))
    evicted = record("other", age=timedelta(days=8))
    with closing(
        connection.Database.connect(**connection.get_connection_params())
    ) as blocker:
        with blocker.cursor() as cursor:
            cursor.execute(
                "SELECT id FROM ws_realtime_events WHERE id = %s FOR UPDATE", [baseline]
            )
        delete_with_old_worker_sql([evicted])
        assert RealtimeEvent.objects.filter(pk=baseline).exists()
        assert not RealtimeEvent.objects.filter(pk=evicted).exists()
        assert RealtimeEventHistoryState.objects.get(pk=1).floor >= evicted
        assert replay(baseline).force_refresh is True


@pytest.mark.parametrize("age_days", [30, 365])
def test_old_sentinels_are_kept_until_a_newer_expired_original_replaces_them(
    monkeypatch, age_days
):
    now = timezone.now()
    monkeypatch.setattr(realtime_events.timezone, "now", lambda: now)
    discarded = record(
        payload=group_event(value="old"), age=timedelta(days=age_days + 1)
    )
    retained = record(
        payload=group_event(value="retained"), age=timedelta(days=age_days)
    )
    original = RealtimeEvent.objects.get(pk=retained)

    assert cleanup() == 1
    assert cleanup() == 0

    assert not RealtimeEvent.objects.filter(pk=discarded).exists()
    sentinel = RealtimeEvent.objects.get()
    assert (sentinel.id, sentinel.payload, sentinel.created_at) == (
        original.id,
        original.payload,
        original.created_at,
    )
    assert sentinel.sentinel_key is not None
    newer = record(
        payload=group_event(value="newest"), age=timedelta(days=age_days - 1)
    )
    replacement = RealtimeEvent.objects.get(pk=newer)

    assert cleanup() == 1

    sentinel = RealtimeEvent.objects.get()
    assert (sentinel.id, sentinel.payload, sentinel.created_at) == (
        replacement.id,
        replacement.payload,
        replacement.created_at,
    )
    assert RealtimeEventHistoryState.objects.get(pk=1).floor == 0


def test_compaction_preserves_a_preexisting_loss_floor():
    lost = record("other")
    delete_with_old_worker_sql([lost])
    record(age=timedelta(days=365))
    retained = record(age=timedelta(days=30))

    assert cleanup() == 1

    assert list(RealtimeEvent.objects.values_list("id", flat=True)) == [retained]
    assert RealtimeEventHistoryState.objects.get(pk=1).floor == lost


def test_concurrent_compaction_cannot_hide_a_relevant_event():
    baseline = record("baseline")
    event_id = record()
    moved = False
    with closing(
        connection.Database.connect(**connection.get_connection_params())
    ) as cleaner:
        cleaner.autocommit = True

        def compact_after_first_read(execute, sql, params, many, context):
            nonlocal moved
            result = execute(sql, params, many, context)
            if (
                not moved
                and sql.lstrip().upper().startswith("SELECT")
                and "ws_realtime_events" in sql
            ):
                moved = True
                with cleaner.cursor() as cursor:
                    cursor.execute(
                        "DELETE FROM ws_realtime_events WHERE id = %s", [event_id]
                    )
            return result

        with connection.execute_wrapper(compact_after_first_read):
            result = replay(baseline)

    assert moved, "The regression must overlap compaction with the actual replay read"
    assert result.force_refresh or event_id in [
        event.id for event in result.replay_events
    ]


@pytest.mark.asyncio
@pytest.mark.parametrize("compacted", [False, True], ids=["full", "compacted"])
@pytest.mark.parametrize(
    "supports_refresh",
    [None, False, True, "true"],
    ids=["absent", "false", "true", "string-true"],
)
async def test_websocket_only_literal_history_capability_recovers_meaningful_events(
    data_fixture, settings, monkeypatch, compacted, supports_refresh
):
    settings.PRESENCE_VISIBLE_USERS = 0
    settings.BASEROW_REALTIME_REPLAY_MAX_EVENTS = 1

    def prepare():
        user, token = data_fixture.create_user_and_token()
        baseline = record("baseline", age=timedelta(days=3))
        history_ids = []
        for index in range(2):
            event = users_event(recipients=[user.id])
            event["payload"] = {
                "type": "row_history_updated",
                "private_history": f"never-replay-history-{index}",
            }
            age = timedelta(days=2) if compacted else timedelta(hours=1)
            history_ids.append(record("users", event, age=age))
        event = users_event(recipients=[user.id])
        event["payload"] = {"type": "workspace_updated", "value": "current"}
        meaningful = record("users", event)
        if compacted:
            cleanup()
            assert (
                list(
                    RealtimeEvent.objects.filter(pk__in=history_ids).values_list(
                        "id", flat=True
                    )
                )
                == history_ids[-1:]
            )
        else:
            assert RealtimeEvent.objects.filter(pk__in=history_ids).count() == 2
        return token, baseline, meaningful

    token, baseline, meaningful = await sync_to_async(prepare)()
    requests = MagicMock()
    monkeypatch.setattr(replay_module, "websocket_replay_requests", requests)
    communicator = WebsocketCommunicator(
        application, f"ws/core/?jwt_token={token}&web_socket_id=own"
    )
    with replay_module.ReplayExecutor(2) as executor:
        monkeypatch.setattr(replay_module, "_executor", executor)
        try:
            assert (await communicator.connect())[0]
            authentication = await communicator.receive_json_from()
            assert authentication["success"] is True
            assert authentication["replay_enabled"] is True
            request = {"type": "replay_events", "last_seen_id": baseline}
            if supports_refresh is not None:
                request["supports_row_history_refresh"] = supports_refresh
            await communicator.send_json_to(request)

            response = await communicator.receive_json_from(timeout=2)
            if supports_refresh is True:
                # The two history updates exceed MAX_EVENTS=1, but this client
                # refetches history and receives exactly the meaningful update.
                assert response == {
                    "type": "workspace_updated",
                    "value": "current",
                    "_event_id": meaningful,
                }
                response = await communicator.receive_json_from(timeout=2)
                assert response == {
                    "type": "replay_events_result",
                    "force_refresh": False,
                    "latest_event_id": meaningful,
                }
            else:
                # Retained expired originals are never emitted as client events,
                # including to older clients.
                assert response == {
                    "type": "replay_events_result",
                    "force_refresh": True,
                    "latest_event_id": NO_REPLAY_AVAILABLE,
                }
            assert await communicator.receive_nothing(timeout=0.05)
            requests.add.assert_called_once_with(
                1,
                {
                    "process.pid": os.getpid(),
                    "outcome": "replayed" if supports_refresh is True else "refresh",
                    "reason": (
                        "none"
                        if supports_refresh is True
                        else "expired_payload"
                        if compacted
                        else "event_limit"
                    ),
                },
            )
        finally:
            await communicator.disconnect(timeout=2)
