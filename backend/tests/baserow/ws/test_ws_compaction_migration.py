import json
from contextlib import closing
from importlib import import_module

from django.db import DatabaseError, OperationalError, connection, transaction

import pytest

from baserow.ws.models import (
    RealtimeEventHistoryState,
    RealtimeEventSummary,
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
            "'ws_realtime_event_summaries'::regclass, "
            "'ws_realtime_event_history_state'::regclass, "
            "pg_get_serial_sequence('ws_realtime_events', 'id')::regclass)"
        )
        persistence = dict(cursor.fetchall())
        assert persistence.pop("ws_realtime_event_summaries") == "u"
        assert persistence.pop("ws_realtime_event_history_state") == "u"
        assert list(persistence.values()) == ["p"]

        cursor.execute(
            "SELECT format_type(atttypid, atttypmod) FROM pg_attribute "
            "WHERE attrelid = 'ws_realtime_event_summaries'::regclass "
            "AND attname = 'key'"
        )
        assert cursor.fetchone()[0] == "bytea"
        cursor.execute(
            "SELECT indexrelid::regclass::text, indisvalid FROM pg_index "
            "WHERE indrelid = 'ws_realtime_event_summaries'::regclass"
        )
        assert dict(cursor.fetchall()) == {
            "ws_realtime_event_summaries_pkey": True,
            "ws_summary_group_event_idx": True,
            "ws_summary_event_idx": True,
            "ws_summary_created_key_idx": True,
            "ws_summary_users_payload_idx": True,
        }

        cursor.execute(
            "SELECT reloptions FROM pg_class "
            "WHERE oid = 'ws_realtime_event_summaries'::regclass"
        )
        options = dict(option.split("=", 1) for option in cursor.fetchone()[0])
        assert (
            options.items()
            >= {
                "autovacuum_analyze_threshold": "2000",
                "autovacuum_analyze_scale_factor": "0.002",
                "autovacuum_vacuum_threshold": "5000",
                "autovacuum_vacuum_scale_factor": "0.01",
                "autovacuum_vacuum_insert_threshold": "5000",
                "autovacuum_vacuum_insert_scale_factor": "0.01",
            }.items()
        )

        cursor.execute(
            "SELECT pg_get_triggerdef(oid), tgenabled FROM pg_trigger "
            "WHERE tgrelid = 'ws_realtime_events'::regclass "
            "AND tgname = 'ws_realtime_events_compact_after_delete'"
        )
        definition, enabled = cursor.fetchone()
    assert "AFTER DELETE" in definition
    assert "FOR EACH STATEMENT" in definition
    assert "REFERENCING OLD TABLE AS ws_deleted_realtime_events" in definition
    assert enabled == "O"


def test_reapplying_migration_preserves_summary_and_history_floor():
    event_id = record()
    with connection.cursor() as cursor:
        cursor.execute("DELETE FROM ws_realtime_events WHERE id = %s", [event_id])
    summary = RealtimeEventSummary.objects.get()
    original = (summary.key, summary.payload, summary.last_event_id, summary.created_at)
    RealtimeEventHistoryState.objects.filter(pk=1).update(floor=event_id)

    for _ in range(2):
        with connection.schema_editor(atomic=True) as editor:
            migration().forwards(None, editor)
        summary.refresh_from_db()
        assert (
            summary.key,
            summary.payload,
            summary.last_event_id,
            summary.created_at,
        ) == original
        assert RealtimeEventHistoryState.objects.get(pk=1).floor == event_id


def test_legacy_delete_compacts_multiple_rows_into_one_canonical_audience():
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
    # This is intentionally raw SQL, as issued by an old cleanup worker. No new
    # application recording/cleanup helper can provide the compaction here.
    with connection.cursor() as cursor:
        cursor.execute(
            "DELETE FROM ws_realtime_events WHERE id IN (%s, %s)", [first, second]
        )

    summary = RealtimeEventSummary.objects.get()
    assert len(summary.key) == 32
    assert summary.last_event_id == second
    assert summary.payload["user_ids"] == [7, 42]
    assert summary.payload["payload"] == {"type": "workspace_updated"}
    assert summary.payload["ignore_web_socket_id"] == "same"
    assert "secret" not in json.dumps(summary.payload)


def test_reversed_delete_order_never_lowers_an_audience_high_water_mark():
    first, second = record(), record()
    with connection.cursor() as cursor:
        cursor.execute("DELETE FROM ws_realtime_events WHERE id = %s", [second])
        cursor.execute("DELETE FROM ws_realtime_events WHERE id = %s", [first])
    assert RealtimeEventSummary.objects.get().last_event_id == second


def test_history_reinitialization_after_data_loss_uses_allocated_sequence_ids():
    committed = record()
    with pytest.raises(RuntimeError, match="rollback"):
        with transaction.atomic():
            allocated = record()
            raise RuntimeError("rollback")
    assert allocated > committed
    # Simulate lost UNLOGGED relation contents, retaining the logged sequence.
    with connection.cursor() as cursor:
        cursor.execute(
            "TRUNCATE ws_realtime_events, ws_realtime_event_summaries, "
            "ws_realtime_event_history_state"
        )
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
