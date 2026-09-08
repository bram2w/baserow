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
    RealtimeEventSummary,
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

    assert not RealtimeEvent.objects.filter(pk__in=[baseline, irrelevant]).exists()
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
def test_expired_payload_and_compact_summary_have_identical_routing(
    group, payload, relevant
):
    baseline = record("baseline", age=timedelta(days=3))
    event_id = record(group, payload, age=timedelta(days=2))

    # Payload time acceptance must not depend on whether Celery ran on time.
    assert replay(baseline).force_refresh is relevant
    cleanup()
    assert not RealtimeEvent.objects.filter(pk=event_id).exists()
    result = replay(baseline)
    assert result.force_refresh is relevant
    assert result.replay_events == []


def test_compaction_collapses_matching_audiences_and_strips_business_data():
    first = record(payload=group_event(value="old-secret"), age=timedelta(days=3))
    second = record(payload=group_event(value="new-secret"), age=timedelta(days=2))
    delete_with_old_worker_sql([first, second])

    summary = RealtimeEventSummary.objects.get()
    assert summary.last_event_id == second
    assert summary.channel_group == "table-1"
    assert summary.payload["payload"] == {"type": "rows_updated"}
    assert "secret" not in str(summary.payload)
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
    delete_with_old_worker_sql([event_id])
    assert replay(baseline).force_refresh is True


def test_compaction_keeps_own_socket_and_exclusion_audiences_distinct():
    ids = [
        record(payload=group_event(own="own")),
        record(payload=group_event(own="other")),
        record(payload=group_event(excluded=[42])),
        record(payload=group_event(excluded=[7])),
    ]
    delete_with_old_worker_sql(ids)
    assert set(
        RealtimeEventSummary.objects.values_list("last_event_id", flat=True)
    ) == set(ids)


def test_compaction_is_atomic_with_a_legacy_delete_statement():
    event_id = record(payload=group_event(value="private"))
    with pytest.raises(RuntimeError, match="rollback"):
        with transaction.atomic():
            delete_with_old_worker_sql([event_id])
            assert not RealtimeEvent.objects.filter(pk=event_id).exists()
            assert RealtimeEventSummary.objects.filter(last_event_id=event_id).exists()
            raise RuntimeError("rollback")

    assert RealtimeEvent.objects.filter(pk=event_id).exists()
    assert not RealtimeEventSummary.objects.exists()
    delete_with_old_worker_sql([event_id])
    assert RealtimeEventSummary.objects.filter(last_event_id=event_id).exists()


@pytest.mark.parametrize("microseconds,replayable", [(0, True), (1, False)])
def test_payload_age_cutoff_is_enforced_without_cleanup(
    monkeypatch, microseconds, replayable
):
    now = timezone.now()
    monkeypatch.setattr(realtime_events.timezone, "now", lambda: now)
    baseline = record("baseline", age=timedelta(days=2), now=now)
    event_id = record(age=timedelta(days=1, microseconds=microseconds), now=now)
    result = replay(baseline)
    assert result.force_refresh is not replayable
    assert [event.id for event in result.replay_events] == (
        [event_id] if replayable else []
    )
    assert RealtimeEvent.objects.filter(pk=event_id).exists()


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
        delete_with_old_worker_sql([baseline, event_id])
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
        delete_with_old_worker_sql([baseline, event_id])
        summary = RealtimeEventSummary.objects.get(channel_group="users")
        assert summary.payload["payload_map"] == {
            "42": {"type": "row_history_updated"},
            "7": {"type": "workspace_updated"},
        }
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


def test_history_expiry_advances_floor_past_a_locked_old_full_baseline():
    baseline = record("baseline", age=timedelta(days=9))
    evicted = record("other", age=timedelta(days=8))
    delete_with_old_worker_sql([evicted])
    RealtimeEventSummary.objects.update(created_at=timezone.now() - timedelta(days=8))
    with closing(
        connection.Database.connect(**connection.get_connection_params())
    ) as blocker:
        with blocker.cursor() as cursor:
            cursor.execute(
                "SELECT id FROM ws_realtime_events WHERE id = %s FOR UPDATE", [baseline]
            )
        cleanup()
        assert RealtimeEvent.objects.filter(pk=baseline).exists()
        assert not RealtimeEventSummary.objects.filter(last_event_id=evicted).exists()
        assert RealtimeEventHistoryState.objects.get(pk=1).floor >= evicted
        assert replay(baseline).force_refresh is True


def test_summary_retention_keeps_the_exact_seven_day_boundary(monkeypatch):
    now = timezone.now()
    monkeypatch.setattr(realtime_events.timezone, "now", lambda: now)
    expired = record("expired", age=timedelta(days=7, microseconds=1), now=now)
    boundary = record("boundary", age=timedelta(days=7), now=now)
    delete_with_old_worker_sql([expired, boundary])

    cleanup()

    assert list(
        RealtimeEventSummary.objects.values_list("last_event_id", flat=True)
    ) == [boundary]
    assert RealtimeEventHistoryState.objects.get(pk=1).floor == expired


def test_summary_expiry_and_floor_advance_roll_back_together():
    expired = record("other", age=timedelta(days=8))
    delete_with_old_worker_sql([expired])

    def fail_after_expiry(execute, sql, params, many, context):
        result = execute(sql, params, many, context)
        if (
            sql.startswith("WITH expired")
            and "UPDATE ws_realtime_event_history_state" in sql
        ):
            raise OperationalError("Failure before expiry transaction committed")
        return result

    with connection.execute_wrapper(fail_after_expiry), pytest.raises(OperationalError):
        cleanup()

    assert RealtimeEventSummary.objects.filter(last_event_id=expired).exists()
    assert RealtimeEventHistoryState.objects.get(pk=1).floor == 0


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
                and (
                    "ws_realtime_events" in sql or "ws_realtime_event_summaries" in sql
                )
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
            assert not RealtimeEvent.objects.filter(pk__in=history_ids).exists()
            assert RealtimeEventSummary.objects.filter(channel_group="users").exists()
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
                # Neither expired business data nor compact routing summaries
                # are emitted as client events, including to older clients.
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
