from contextlib import closing
from datetime import timedelta
from unittest.mock import patch

from django.db import OperationalError, connection, transaction
from django.utils import timezone

import pytest

from baserow.ws import realtime_events, tasks
from baserow.ws.models import RealtimeEvent
from baserow.ws.realtime_events import RealtimeEventHandler
from baserow.ws.tasks import cleanup_old_realtime_events


@pytest.mark.parametrize("max_events", [0, 5])
def test_cleanup_task_uses_independent_retention_even_when_recording_disabled(
    settings, max_events
):
    settings.BASEROW_REALTIME_REPLAY_MAX_EVENTS = max_events
    settings.SIMPLE_JWT = {"REFRESH_TOKEN_LIFETIME": timedelta(days=7)}
    with (
        patch.object(RealtimeEventHandler, "cleanup_old_realtime_events") as cleanup,
        patch("django.core.cache.cache.lock"),
        patch.object(tasks, "monotonic", return_value=100),
    ):
        cleanup_old_realtime_events()
    cleanup.assert_called_once_with(timedelta(hours=24), deadline=130)


def test_cleanup_task_skips_an_overlapping_run():
    with (
        patch.object(RealtimeEventHandler, "cleanup_old_realtime_events") as cleanup,
        patch("django.core.cache.cache.lock") as make_lock,
    ):
        lock = make_lock.return_value
        lock.acquire.return_value = False
        cleanup_old_realtime_events()
    lock.acquire.assert_called_once_with(blocking=False)
    cleanup.assert_not_called()
    lock.release.assert_not_called()


def test_cleanup_task_releases_lock_after_failure():
    with (
        patch.object(
            RealtimeEventHandler,
            "cleanup_old_realtime_events",
            side_effect=OperationalError("cleanup failed"),
        ),
        patch("django.core.cache.cache.lock") as make_lock,
    ):
        with pytest.raises(OperationalError):
            cleanup_old_realtime_events()
    make_lock.return_value.release.assert_called_once_with()


def test_cleanup_task_does_not_restart_budget_after_acquiring_lock(monkeypatch):
    now = 0
    monkeypatch.setattr(tasks, "monotonic", lambda: now, raising=False)
    monkeypatch.setattr(realtime_events, "monotonic", lambda: now)

    def delayed_acquire(**kwargs):
        nonlocal now
        now = realtime_events.REALTIME_EVENTS_CLEANUP_LOCK_SECONDS + 1
        return True

    with (
        patch("django.core.cache.cache.lock") as make_lock,
        patch.object(
            RealtimeEventHandler, "_delete_realtime_events_batch", return_value=0
        ) as batch,
    ):
        make_lock.return_value.acquire.side_effect = delayed_acquire
        assert cleanup_old_realtime_events() == 0
    batch.assert_not_called()


def create_events(age, count):
    events = RealtimeEvent.objects.bulk_create(
        [RealtimeEvent(channel_group="table-1", payload={}) for _ in range(count)]
    )
    RealtimeEvent.objects.filter(id__in=[event.id for event in events]).update(
        created_at=timezone.now() - age
    )
    return [event.id for event in events]


@pytest.mark.django_db(transaction=True)
def test_cleanup_commits_bounded_batches_and_preserves_recent_events(monkeypatch):
    monkeypatch.setattr(realtime_events, "REALTIME_EVENTS_CLEANUP_BATCH_SIZE", 2)
    expired = create_events(timedelta(days=2), 5)
    recent = create_events(timedelta(hours=1), 1)
    committed_batches = []
    original = RealtimeEventHandler._delete_realtime_events_batch

    def record_committed_batch(*args):
        deleted = original(*args)
        assert not connection.in_atomic_block
        committed_batches.append(deleted)
        return deleted

    with patch.object(
        RealtimeEventHandler,
        "_delete_realtime_events_batch",
        side_effect=record_committed_batch,
    ):
        assert RealtimeEventHandler.cleanup_old_realtime_events(timedelta(days=1)) == 5
    assert committed_batches == [2, 2, 1]
    assert not RealtimeEvent.objects.filter(id__in=expired).exists()
    assert list(RealtimeEvent.objects.values_list("id", flat=True)) == recent


@pytest.mark.django_db(transaction=True)
def test_cleanup_keeps_earlier_commits_when_a_later_batch_fails(monkeypatch):
    monkeypatch.setattr(realtime_events, "REALTIME_EVENTS_CLEANUP_BATCH_SIZE", 2)
    expired = create_events(timedelta(days=2), 5)
    original = RealtimeEventHandler._delete_realtime_events_batch
    calls = 0

    def fail_second_batch(*args):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OperationalError("second batch failed")
        return original(*args)

    with (
        patch.object(
            RealtimeEventHandler,
            "_delete_realtime_events_batch",
            side_effect=fail_second_batch,
        ),
        pytest.raises(OperationalError, match="second batch failed"),
    ):
        RealtimeEventHandler.cleanup_old_realtime_events(timedelta(days=1))
    assert (
        list(RealtimeEvent.objects.order_by("id").values_list("id", flat=True))
        == expired[2:]
    )


@pytest.mark.django_db(transaction=True)
def test_retention_boundary_preserves_fresh_replay_and_expires_old_cursor(settings):
    settings.SIMPLE_JWT = {"REFRESH_TOKEN_LIFETIME": timedelta(days=7)}
    now = timezone.now()
    with patch.object(realtime_events.timezone, "now", return_value=now):
        expired = create_events(timedelta(hours=24, microseconds=1), 1)[0]
        boundary = create_events(timedelta(hours=24), 1)[0]
        fresh = create_events(timedelta(hours=1), 1)[0]
        latest = create_events(timedelta(minutes=30), 1)[0]

        assert cleanup_old_realtime_events() == 1

    assert list(RealtimeEvent.objects.order_by("id").values_list("id", flat=True)) == [
        boundary,
        fresh,
        latest,
    ]
    expired_result = RealtimeEventHandler.get_replay_events_result(
        1, ["table-1"], expired, None
    )
    assert expired_result.force_refresh is True
    assert expired_result.replay_events == []
    for cursor, expected in ((boundary, [fresh, latest]), (fresh, [latest])):
        result = RealtimeEventHandler.get_replay_events_result(
            1, ["table-1"], cursor, None
        )
        assert result.force_refresh is False
        assert result.latest_event_id == latest
        assert [event.id for event in result.replay_events] == expected


@pytest.mark.django_db(transaction=True)
def test_cleanup_stops_at_its_work_budget(monkeypatch):
    monkeypatch.setattr(realtime_events, "REALTIME_EVENTS_CLEANUP_BATCH_SIZE", 2)
    create_events(timedelta(days=2), 5)
    now = 0
    monkeypatch.setattr(realtime_events, "monotonic", lambda: now)
    original = RealtimeEventHandler._delete_realtime_events_batch

    def consume_budget(*args):
        nonlocal now
        deleted = original(*args)
        now += realtime_events.REALTIME_EVENTS_CLEANUP_BUDGET_SECONDS
        return deleted

    with patch.object(
        RealtimeEventHandler,
        "_delete_realtime_events_batch",
        side_effect=consume_budget,
    ):
        assert RealtimeEventHandler.cleanup_old_realtime_events(timedelta(days=1)) == 2
    assert RealtimeEvent.objects.count() == 3


@pytest.mark.django_db(transaction=True)
def test_cleanup_cannot_be_nested_in_a_larger_transaction():
    with (
        transaction.atomic(),
        pytest.raises(RuntimeError, match="durable atomic block"),
    ):
        RealtimeEventHandler.cleanup_old_realtime_events(timedelta(days=1))


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    "statement_timeout,lock_timeout", [("0", "0"), ("10ms", "5ms")]
)
def test_cleanup_timeouts_are_local_and_preserve_stricter_settings(
    statement_timeout, lock_timeout
):
    observed = []

    def check_timeouts(execute, sql, params, many, context):
        if sql.startswith("WITH expired"):
            with connection.cursor() as cursor:
                cursor.execute("SHOW statement_timeout")
                statement = cursor.fetchone()[0]
                cursor.execute("SHOW lock_timeout")
                lock = cursor.fetchone()[0]
            observed.append((statement, lock))
        return execute(sql, params, many, context)

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT set_config('statement_timeout', %s, false)", [statement_timeout]
        )
        cursor.execute("SELECT set_config('lock_timeout', %s, false)", [lock_timeout])
    try:
        with connection.execute_wrapper(check_timeouts):
            assert (
                RealtimeEventHandler.cleanup_old_realtime_events(timedelta(days=1)) == 0
            )
        assert observed == [
            ("3s", "250ms") if statement_timeout == "0" else ("10ms", "5ms")
        ]
        with connection.cursor() as cursor:
            cursor.execute("SHOW statement_timeout")
            assert cursor.fetchone()[0] == statement_timeout
            cursor.execute("SHOW lock_timeout")
            assert cursor.fetchone()[0] == lock_timeout
    finally:
        connection.close()


@pytest.mark.django_db(transaction=True)
def test_cleanup_statement_timeout_stops_slow_database_work(monkeypatch):
    monkeypatch.setattr(
        realtime_events, "REALTIME_EVENTS_CLEANUP_STATEMENT_TIMEOUT_MS", 25
    )
    expired = create_events(timedelta(days=2), 1)

    def slow_delete(execute, sql, params, many, context):
        if sql.startswith("WITH expired"):
            return execute("SELECT pg_sleep(1)", [], many, context)
        return execute(sql, params, many, context)

    with (
        connection.execute_wrapper(slow_delete),
        pytest.raises(OperationalError) as error,
    ):
        RealtimeEventHandler.cleanup_old_realtime_events(timedelta(days=1))
    cause = error.value.__cause__
    assert (
        getattr(cause, "pgcode", None) or getattr(cause, "sqlstate", None)
    ) == "57014"
    assert list(RealtimeEvent.objects.values_list("id", flat=True)) == expired


@pytest.mark.django_db(transaction=True)
def test_cleanup_lock_timeout_does_not_wait_for_table_maintenance(monkeypatch):
    monkeypatch.setattr(realtime_events, "REALTIME_EVENTS_CLEANUP_LOCK_TIMEOUT_MS", 25)
    expired = create_events(timedelta(days=2), 1)
    with closing(
        connection.Database.connect(**connection.get_connection_params())
    ) as blocker:
        with blocker.cursor() as cursor:
            cursor.execute("LOCK TABLE ws_realtime_events IN ACCESS EXCLUSIVE MODE")
        with pytest.raises(OperationalError) as error:
            RealtimeEventHandler.cleanup_old_realtime_events(timedelta(days=1))
        cause = error.value.__cause__
        assert (
            getattr(cause, "pgcode", None) or getattr(cause, "sqlstate", None)
        ) == "55P03"
    assert list(RealtimeEvent.objects.values_list("id", flat=True)) == expired
    assert RealtimeEventHandler.cleanup_old_realtime_events(timedelta(days=1)) == 1


@pytest.mark.django_db(transaction=True)
def test_cleanup_skips_locked_rows_and_cleans_them_on_a_later_run():
    expired = create_events(timedelta(days=2), 3)
    with closing(
        connection.Database.connect(**connection.get_connection_params())
    ) as blocker:
        with blocker.cursor() as cursor:
            cursor.execute(
                "SELECT id FROM ws_realtime_events WHERE id = %s FOR UPDATE",
                [expired[0]],
            )
        assert RealtimeEventHandler.cleanup_old_realtime_events(timedelta(days=1)) == 2
        assert list(RealtimeEvent.objects.values_list("id", flat=True)) == [expired[0]]
    assert RealtimeEventHandler.cleanup_old_realtime_events(timedelta(days=1)) == 1
