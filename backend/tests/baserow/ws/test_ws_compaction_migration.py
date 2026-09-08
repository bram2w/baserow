from contextlib import closing
from datetime import timedelta
from importlib import import_module

from django.db import DatabaseError, OperationalError, connection, transaction
from django.utils import timezone

import pytest

from baserow.ws.models import (
    RealtimeEvent,
    RealtimeEventHistoryState,
)
from baserow.ws.realtime_events import RealtimeEventHandler

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.websockets]


def migration():
    return import_module("baserow.ws.migrations.0003_realtime_event_compaction")


def record(payload=None):
    return RealtimeEventHandler.record_events(
        [
            (
                "users",
                payload
                or {
                    "type": "broadcast_to_users",
                    "user_ids": [42],
                    "send_to_all_users": False,
                    "ignore_web_socket_id": None,
                    "payload": {"type": "workspace_updated", "data": "private"},
                },
            )
        ]
    )[0]


def test_compaction_catalog_keeps_history_unlogged_and_event_sequence_logged():
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT relname, relpersistence FROM pg_class WHERE oid IN ("
            "'ws_realtime_event_history_state'::regclass, "
            "pg_get_serial_sequence('ws_realtime_events', 'id')::regclass)"
        )
        persistence = dict(cursor.fetchall())
        assert persistence.pop("ws_realtime_event_history_state") == "u"
        assert list(persistence.values()) == ["p"]

        cursor.execute(
            "SELECT format_type(atttypid, atttypmod), attnotnull FROM pg_attribute "
            "WHERE attrelid = 'ws_realtime_events'::regclass "
            "AND attname = 'sentinel_key'"
        )
        assert cursor.fetchone() == ("bytea", False)
        cursor.execute(
            "SELECT indexrelid::regclass::text, indisvalid, indisunique, "
            "pg_get_expr(indpred, indrelid) FROM pg_index "
            "WHERE indexrelid IN ('ws_realtime_sentinel_key_uniq'::regclass, "
            "'ws_realtime_pending_age_idx'::regclass)"
        )
        assert {name: values for name, *values in cursor.fetchall()} == {
            "ws_realtime_sentinel_key_uniq": [True, True, "(sentinel_key IS NOT NULL)"],
            "ws_realtime_pending_age_idx": [True, False, "(sentinel_key IS NULL)"],
        }
        cursor.execute(
            "SELECT pg_get_triggerdef(oid), tgenabled FROM pg_trigger "
            "WHERE tgrelid = 'ws_realtime_events'::regclass "
            "AND tgname = 'ws_realtime_events_history_after_delete'"
        )
        definition, enabled = cursor.fetchone()
    assert "AFTER DELETE" in definition
    assert "FOR EACH STATEMENT" in definition
    assert "REFERENCING OLD TABLE AS ws_deleted_realtime_events" in definition
    assert enabled == "O"


def test_reapplying_migration_preserves_original_sentinel_and_history_floor():
    event_id = record()
    RealtimeEvent.objects.filter(pk=event_id).update(
        created_at=timezone.now() - timedelta(days=2)
    )
    RealtimeEventHandler.cleanup_old_realtime_events(timedelta(days=1))
    original = RealtimeEvent.objects.values().get(pk=event_id)
    RealtimeEventHistoryState.objects.filter(pk=1).update(floor=event_id)

    for _ in range(2):
        with connection.schema_editor(atomic=False) as editor:
            migration().forwards(None, editor)
        assert RealtimeEvent.objects.values().get(pk=event_id) == original
        assert RealtimeEventHistoryState.objects.get(pk=1).floor == event_id


def test_compaction_uses_canonical_audience_but_preserves_original_payload():
    first = record(
        {
            "type": "broadcast_to_users",
            "user_ids": [42, 7, 42],
            "send_to_all_users": False,
            "ignore_web_socket_id": "same",
            "payload": {"type": "workspace_updated", "data": "first-secret"},
        }
    )
    second = record(
        {
            "type": "broadcast_to_users",
            "user_ids": [7, 42],
            "send_to_all_users": False,
            "ignore_web_socket_id": "same",
            "payload": {"type": "workspace_updated", "data": "second-secret"},
        }
    )
    RealtimeEvent.objects.filter(pk__in=[first, second]).update(
        created_at=timezone.now() - timedelta(days=2)
    )
    original = RealtimeEvent.objects.get(pk=second)

    assert RealtimeEventHandler.cleanup_old_realtime_events(timedelta(days=1)) == 1

    retained = RealtimeEvent.objects.get()
    assert len(retained.sentinel_key) == 32
    assert retained.id == second
    assert retained.payload == original.payload
    assert retained.created_at == original.created_at
    assert RealtimeEventHistoryState.objects.get(pk=1).floor == 0


def test_reversed_legacy_delete_order_never_lowers_the_loss_floor():
    first, second = record(), record()
    with connection.cursor() as cursor:
        cursor.execute("DELETE FROM ws_realtime_events WHERE id = %s", [second])
        cursor.execute("DELETE FROM ws_realtime_events WHERE id = %s", [first])
    assert RealtimeEventHistoryState.objects.get(pk=1).floor == second


def test_history_reinitialization_after_data_loss_uses_allocated_sequence_ids():
    committed = record()
    with pytest.raises(RuntimeError, match="rollback"):
        with transaction.atomic():
            allocated = record()
            raise RuntimeError("rollback")
    assert allocated > committed
    # Simulate lost UNLOGGED relation contents, retaining the logged sequence.
    with connection.cursor() as cursor:
        cursor.execute("TRUNCATE ws_realtime_events, ws_realtime_event_history_state")
        cursor.execute("SELECT ws_initialize_realtime_history()")
    floor = RealtimeEventHistoryState.objects.get(pk=1).floor
    assert floor >= allocated
    assert record() > floor


def test_repeated_history_initialization_does_not_move_an_existing_floor():
    floor = RealtimeEventHistoryState.objects.get(pk=1).floor
    record()
    with connection.cursor() as cursor:
        cursor.execute("SELECT ws_initialize_realtime_history()")
        cursor.execute("SELECT ws_initialize_realtime_history()")
    assert RealtimeEventHistoryState.objects.get(pk=1).floor == floor


def test_history_initialization_waits_for_inflight_inserts():
    RealtimeEventHistoryState.objects.all().delete()
    with closing(
        connection.Database.connect(**connection.get_connection_params())
    ) as writer:
        with writer.cursor() as cursor:
            cursor.execute(
                "INSERT INTO ws_realtime_events (channel_group, payload, created_at) "
                "VALUES ('other', '{}', now()) RETURNING id"
            )
            inserted_id = cursor.fetchone()[0]

        # The uncommitted INSERT owns a RowExclusive table lock. Initialization
        # must wait rather than establish coverage while that writer is invisible.
        with pytest.raises(OperationalError) as error:
            with transaction.atomic(), connection.cursor() as cursor:
                cursor.execute("SET LOCAL lock_timeout = '25ms'")
                cursor.execute("SELECT ws_initialize_realtime_history()")
        cause = error.value.__cause__
        assert (
            getattr(cause, "pgcode", None) or getattr(cause, "sqlstate", None)
        ) == "55P03"
        assert not RealtimeEventHistoryState.objects.exists()
        writer.commit()

    with connection.cursor() as cursor:
        cursor.execute("SELECT ws_initialize_realtime_history()")
    assert RealtimeEventHistoryState.objects.get(pk=1).floor >= inserted_id


def test_missing_history_with_cached_sequence_ids_fails_closed():
    RealtimeEventHistoryState.objects.all().delete()
    with connection.cursor() as cursor:
        cursor.execute(
            "DO $block$ BEGIN EXECUTE format('ALTER SEQUENCE %s CACHE 100', "
            "pg_get_serial_sequence('ws_realtime_events', 'id')); END $block$"
        )
    try:
        with (
            connection.cursor() as cursor,
            pytest.raises(DatabaseError, match="CACHE 1"),
        ):
            cursor.execute("SELECT ws_initialize_realtime_history()")
        assert not RealtimeEventHistoryState.objects.exists()
    finally:
        with connection.cursor() as cursor:
            cursor.execute(
                "DO $block$ BEGIN EXECUTE format('ALTER SEQUENCE %s CACHE 1', "
                "pg_get_serial_sequence('ws_realtime_events', 'id')); END $block$"
            )
            cursor.execute("SELECT ws_initialize_realtime_history()")
