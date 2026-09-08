from importlib import import_module
from unittest.mock import patch

from django.db import IntegrityError, connection

import pytest

from baserow.ws.models import RealtimeEvent
from baserow.ws.realtime_events import RealtimeEventHandler


def _migration():
    return import_module("baserow.ws.migrations.0002_realtime_event_indexes")


def _indexes():
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT c.relname, i.indisvalid AND i.indisready,
                pg_get_expr(i.indpred, i.indrelid), pg_get_indexdef(i.indexrelid)
            FROM pg_index i JOIN pg_class c ON c.oid = i.indexrelid
            WHERE i.indrelid = 'ws_realtime_events'::regclass
            """
        )
        return {
            name: (valid, predicate, definition)
            for name, valid, predicate, definition in cursor
        }


def _apply(direction):
    with connection.schema_editor(atomic=False) as editor:
        getattr(_migration(), direction)(None, editor)


def _table_storage():
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT relfilenode, reloptions FROM pg_class "
            "WHERE oid = 'ws_realtime_events'::regclass"
        )
        filenode, options = cursor.fetchone()
        return filenode, dict(option.split("=", 1) for option in options or [])


@pytest.mark.django_db(transaction=True)
def test_replay_autovacuum_settings_are_reversible_and_retry_safe():
    expected = {
        "autovacuum_analyze_threshold": "2000",
        "autovacuum_analyze_scale_factor": "0.002",
        "autovacuum_vacuum_threshold": "5000",
        "autovacuum_vacuum_scale_factor": "0.01",
        "autovacuum_vacuum_insert_threshold": "5000",
        "autovacuum_vacuum_insert_scale_factor": "0.01",
    }
    filenode, original_options = _table_storage()
    unrelated = {
        name: value for name, value in original_options.items() if name not in expected
    }
    unrelated["fillfactor"] = "80"
    with connection.cursor() as cursor:
        cursor.execute("ALTER TABLE ws_realtime_events SET (fillfactor = 80)")
    try:
        _apply("backwards")
        assert _table_storage() == (filenode, unrelated)

        for _ in range(2):
            _apply("forwards")
            assert _table_storage() == (filenode, {**unrelated, **expected})

        for _ in range(2):
            _apply("backwards")
            assert _table_storage() == (filenode, unrelated)
    finally:
        _apply("forwards")
        with connection.cursor() as cursor:
            if "fillfactor" in original_options:
                cursor.execute(
                    "ALTER TABLE ws_realtime_events SET "
                    f"(fillfactor = {int(original_options['fillfactor'])})"
                )
            else:
                cursor.execute("ALTER TABLE ws_realtime_events RESET (fillfactor)")


@pytest.mark.django_db(transaction=True)
def test_replay_index_upgrade_and_rollback_preserve_delivery():
    migration = _migration()
    _apply("backwards")
    try:
        baseline = RealtimeEvent.objects.create(channel_group="other", payload={})

        def group(label, **kwargs):
            return (
                "table-1",
                {
                    "type": "broadcast_to_group",
                    "payload": {"label": label},
                    "ignore_web_socket_id": None,
                    **kwargs,
                },
            )

        def users(label, **kwargs):
            return (
                "users",
                {
                    "type": "broadcast_to_users",
                    "payload": {"label": label},
                    "user_ids": [42],
                    "send_to_all_users": False,
                    "ignore_web_socket_id": None,
                    **kwargs,
                },
            )

        def individual(label, recipient="42", **kwargs):
            return (
                "users",
                {
                    "type": "broadcast_to_users_individual_payloads",
                    "payload_map": {recipient: {"label": label}},
                    "ignore_web_socket_id": None,
                    **kwargs,
                },
            )

        events = RealtimeEventHandler.record_events(
            [
                group("page"),
                group("own-page", ignore_web_socket_id="same-socket"),
                group("excluded-page", exclude_user_ids=[42]),
                users("all-users", user_ids=[], send_to_all_users=True),
                users("target-user"),
                users("another-user", user_ids=[7]),
                users("own-user", ignore_web_socket_id="same-socket"),
                individual("individual"),
                individual("another-individual", recipient="7"),
                individual("own-individual", ignore_web_socket_id="same-socket"),
            ]
        )

        def replay_ids():
            return list(
                RealtimeEventHandler.get_replay_window(
                    42, ["table-1"], baseline.id, "same-socket"
                ).values_list("id", flat=True)
            )

        expected = [baseline.id, events[0], events[3], events[4], events[7]]
        assert replay_ids() == expected
        assert migration.OLD_INDEX in _indexes()

        _apply("forwards")
        _apply("forwards")  # Retry after a completed but not recorded migration.
        indexes = _indexes()
        assert migration.OLD_INDEX not in indexes
        valid, predicate, definition = indexes[migration.USERS_INDEX]
        assert valid
        assert "channel_group" in predicate and "'users'" in predicate
        assert "USING gin (payload jsonb_path_ops)" in definition
        valid, predicate, definition = indexes[migration.CREATED_INDEX]
        assert valid and predicate is None
        assert "USING btree (created_at, id)" in definition
        assert replay_ids() == expected

        _apply("backwards")
        indexes = _indexes()
        assert indexes[migration.OLD_INDEX][0]
        assert indexes[migration.OLD_INDEX][1] is None
        assert migration.USERS_INDEX not in indexes
        assert migration.CREATED_INDEX not in indexes
        assert replay_ids() == expected
    finally:
        _apply("forwards")


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    "index_name", ["ws_realtime_users_payload_idx", "ws_realtime_created_id_idx"]
)
def test_replay_index_migration_rebuilds_an_invalid_concurrent_index(index_name):
    _apply("backwards")
    try:
        RealtimeEventHandler.record_events([("table-1", {}), ("table-1", {})])
        # A failed concurrent uniqueness check leaves the same unusable catalog
        # state as an interrupted concurrent build, without editing pg_index.
        with connection.cursor() as cursor, pytest.raises(IntegrityError):
            cursor.execute(
                f'CREATE UNIQUE INDEX CONCURRENTLY "{index_name}" ON ws_realtime_events (channel_group)'
            )
        assert _indexes()[index_name][0] is False
        _apply("forwards")
        assert _indexes()[index_name][0] is True
        assert _migration().OLD_INDEX not in _indexes()
    finally:
        _apply("forwards")


@pytest.mark.django_db(transaction=True)
def test_interrupted_replay_index_upgrade_keeps_old_index_until_both_are_ready():
    migration = _migration()
    _apply("backwards")
    create_index = migration._create_index

    def fail_second_build(cursor, name, definition):
        if name == migration.CREATED_INDEX:
            raise RuntimeError("Interrupted between concurrent builds")
        create_index(cursor, name, definition)

    try:
        with patch.object(migration, "_create_index", side_effect=fail_second_build):
            with pytest.raises(RuntimeError, match="Interrupted"):
                _apply("forwards")
        indexes = _indexes()
        assert indexes[migration.OLD_INDEX][0]
        assert indexes[migration.USERS_INDEX][0]
        assert migration.CREATED_INDEX not in indexes
        _apply("forwards")
        indexes = _indexes()
        assert indexes[migration.CREATED_INDEX][0]
        assert migration.OLD_INDEX not in indexes
    finally:
        _apply("forwards")
