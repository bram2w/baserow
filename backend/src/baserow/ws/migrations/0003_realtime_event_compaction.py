from django.contrib.postgres.indexes import GinIndex
from django.db import migrations, models
from django.db.models.functions import Now

INITIALIZE_HISTORY = """
CREATE OR REPLACE FUNCTION ws_initialize_realtime_history() RETURNS void
LANGUAGE plpgsql AS $function$
DECLARE
    event_sequence regclass;
    sequence_value bigint;
    sequence_called boolean;
BEGIN
    IF EXISTS (SELECT 1 FROM ws_realtime_event_history_state WHERE id = 1) THEN
        RETURN;
    END IF;
    -- Only initialization takes this lock. Pending INSERTs must finish before
    -- their allocated IDs can become the floor returned to a fresh connection.
    LOCK TABLE ws_realtime_events IN SHARE MODE;
    IF EXISTS (SELECT 1 FROM ws_realtime_event_history_state WHERE id = 1) THEN
        RETURN;
    END IF;
    event_sequence := pg_get_serial_sequence('ws_realtime_events', 'id')::regclass;
    IF NOT EXISTS (
        SELECT 1 FROM pg_sequence WHERE seqrelid = event_sequence AND seqcache = 1
    ) THEN
        RAISE EXCEPTION 'Realtime history requires CACHE 1 for the event sequence';
    END IF;
    EXECUTE format('SELECT last_value, is_called FROM %s', event_sequence)
        INTO sequence_value, sequence_called;
    INSERT INTO ws_realtime_event_history_state (id, floor)
    VALUES (1, CASE WHEN sequence_called THEN sequence_value ELSE 0 END)
    ON CONFLICT (id) DO NOTHING;
END;
$function$;
"""

ROUTING_PAYLOAD = """
CREATE OR REPLACE FUNCTION ws_realtime_event_routing(event_payload jsonb)
RETURNS jsonb LANGUAGE sql IMMUTABLE STRICT AS $function$
    SELECT jsonb_build_object(
        'type', event_payload->'type',
        'ignore_web_socket_id', event_payload->'ignore_web_socket_id',
        'send_to_all_users', COALESCE(event_payload->'send_to_all_users', 'false'),
        'user_ids', (
            SELECT COALESCE(jsonb_agg(value ORDER BY value), '[]')
            FROM (
                SELECT DISTINCT value FROM jsonb_array_elements(
                    CASE WHEN jsonb_typeof(event_payload->'user_ids') = 'array'
                    THEN event_payload->'user_ids' ELSE '[]' END
                )
            ) AS recipients
        ),
        'exclude_user_ids', (
            SELECT COALESCE(jsonb_agg(value ORDER BY value), '[]')
            FROM (
                SELECT DISTINCT value FROM jsonb_array_elements(
                    CASE WHEN jsonb_typeof(event_payload->'exclude_user_ids') = 'array'
                    THEN event_payload->'exclude_user_ids' ELSE '[]' END
                )
            ) AS excluded
        ),
        'payload', jsonb_build_object('type', event_payload #> '{payload,type}'),
        'payload_map', (
            SELECT COALESCE(jsonb_object_agg(
                recipient, jsonb_build_object('type', message->'type')
            ), '{}')
            FROM jsonb_each(
                CASE WHEN jsonb_typeof(event_payload->'payload_map') = 'object'
                THEN event_payload->'payload_map' ELSE '{}' END
            ) AS messages(recipient, message)
        )
    );
$function$;
"""

COMPACT_DELETED_EVENTS = """
CREATE OR REPLACE FUNCTION ws_compact_deleted_realtime_events() RETURNS trigger
LANGUAGE plpgsql AS $function$
DECLARE
    expected_count bigint;
    written_count bigint;
BEGIN
    PERFORM ws_initialize_realtime_history();
    WITH routed AS MATERIALIZED (
        SELECT channel_group, ws_realtime_event_routing(payload) AS payload,
               id, created_at
        FROM ws_deleted_realtime_events
    ), summarized AS MATERIALIZED (
        SELECT sha256(convert_to(
                   jsonb_build_array(channel_group, payload)::text, 'UTF8'
               )) AS key,
               channel_group, payload, max(id) AS last_event_id,
               max(created_at) AS created_at
        FROM routed GROUP BY channel_group, payload
    ), written AS (
        INSERT INTO ws_realtime_event_summaries AS existing
            (key, channel_group, payload, last_event_id, created_at)
        SELECT key, channel_group, payload, last_event_id, created_at
        FROM summarized ORDER BY key
        ON CONFLICT (key) DO UPDATE SET
            last_event_id = greatest(existing.last_event_id, EXCLUDED.last_event_id),
            created_at = greatest(existing.created_at, EXCLUDED.created_at)
        WHERE existing.channel_group = EXCLUDED.channel_group
          AND existing.payload = EXCLUDED.payload
        RETURNING key
    )
    SELECT (SELECT count(*) FROM summarized), (SELECT count(*) FROM written)
    INTO expected_count, written_count;
    -- A hash collision must abort deletion, never silently lose an audience.
    IF expected_count <> written_count THEN
        RAISE EXCEPTION 'Realtime history summary key collision';
    END IF;
    RETURN NULL;
END;
$function$;
"""


def _set_timeouts(cursor):
    # New tables are empty. Bound the brief existing-table/sequence DDL locks,
    # preserving any stricter operator limit for this migration transaction.
    cursor.execute(
        "SELECT "
        "set_config('lock_timeout', CASE WHEN "
        "current_setting('lock_timeout')::interval = interval '0' OR "
        "current_setting('lock_timeout')::interval > interval '1 second' "
        "THEN '1s' ELSE current_setting('lock_timeout') END, true), "
        "set_config('statement_timeout', CASE WHEN "
        "current_setting('statement_timeout')::interval = interval '0' OR "
        "current_setting('statement_timeout')::interval > interval '3 seconds' "
        "THEN '3s' ELSE current_setting('statement_timeout') END, true)"
    )


def forwards(apps, schema_editor):
    with schema_editor.connection.cursor() as cursor:
        _set_timeouts(cursor)
        # Block old cleanup and INSERTs only for installation. No DELETE may slip
        # between the initial floor and activation of its atomic summary trigger.
        cursor.execute("LOCK TABLE ws_realtime_events IN SHARE ROW EXCLUSIVE MODE")
        cursor.execute("ALTER TABLE ws_realtime_event_summaries SET UNLOGGED")
        cursor.execute("ALTER TABLE ws_realtime_event_history_state SET UNLOGGED")
        # Match 0002/database.0209: frequently updated summaries need fresh
        # planner statistics and prompt reclamation of dead row versions.
        cursor.execute(
            """
            ALTER TABLE ws_realtime_event_summaries SET (
                autovacuum_analyze_threshold = 2000,
                autovacuum_analyze_scale_factor = 0.002,
                autovacuum_vacuum_threshold = 5000,
                autovacuum_vacuum_scale_factor = 0.01,
                autovacuum_vacuum_insert_threshold = 5000,
                autovacuum_vacuum_insert_scale_factor = 0.01
            )
            """
        )
        # 0001's SET UNLOGGED also changed the owned sequence. Keep IDs durable
        # even when the event/summary/state tables are truncated after a crash.
        # PostgreSQL 14 has only logged sequences and no SET LOGGED syntax.
        cursor.execute(
            "DO $block$ DECLARE event_sequence regclass; BEGIN "
            "event_sequence := pg_get_serial_sequence("
            "'ws_realtime_events', 'id')::regclass; "
            "IF EXISTS (SELECT 1 FROM pg_class "
            "WHERE oid = event_sequence AND relpersistence <> 'p') THEN "
            "EXECUTE format('ALTER SEQUENCE %s SET LOGGED', event_sequence); "
            "END IF; END $block$"
        )
        cursor.execute(INITIALIZE_HISTORY)
        cursor.execute(ROUTING_PAYLOAD)
        cursor.execute(COMPACT_DELETED_EVENTS)
        cursor.execute("SELECT ws_initialize_realtime_history()")
        cursor.execute(
            "DROP TRIGGER IF EXISTS ws_realtime_events_compact_after_delete "
            "ON ws_realtime_events"
        )
        cursor.execute(
            "CREATE TRIGGER ws_realtime_events_compact_after_delete "
            "AFTER DELETE ON ws_realtime_events "
            "REFERENCING OLD TABLE AS ws_deleted_realtime_events "
            "FOR EACH STATEMENT EXECUTE FUNCTION ws_compact_deleted_realtime_events()"
        )


def backwards(apps, schema_editor):
    with schema_editor.connection.cursor() as cursor:
        _set_timeouts(cursor)
        cursor.execute("LOCK TABLE ws_realtime_events IN SHARE ROW EXCLUSIVE MODE")
        cursor.execute(
            "DROP TRIGGER IF EXISTS ws_realtime_events_compact_after_delete "
            "ON ws_realtime_events"
        )
        cursor.execute("DROP FUNCTION IF EXISTS ws_compact_deleted_realtime_events()")
        cursor.execute("DROP FUNCTION IF EXISTS ws_realtime_event_routing(jsonb)")
        cursor.execute("DROP FUNCTION IF EXISTS ws_initialize_realtime_history()")
        # Do not return the sequence to UNLOGGED: rollback must not reintroduce
        # reuse of cursor IDs after an unclean PostgreSQL restart.


class Migration(migrations.Migration):
    dependencies = [("ws", "0002_realtime_event_indexes")]

    operations = [
        migrations.CreateModel(
            name="RealtimeEventSummary",
            fields=[
                (
                    "key",
                    models.BinaryField(
                        db_default=b"", primary_key=True, serialize=False
                    ),
                ),
                ("channel_group", models.TextField(db_default="")),
                ("payload", models.JSONField(db_default={})),
                ("last_event_id", models.BigIntegerField(db_default=0)),
                ("created_at", models.DateTimeField(db_default=Now())),
            ],
            options={
                "db_table": "ws_realtime_event_summaries",
                "indexes": [
                    models.Index(
                        fields=["channel_group", "last_event_id"],
                        name="ws_summary_group_event_idx",
                    ),
                    models.Index(fields=["last_event_id"], name="ws_summary_event_idx"),
                    models.Index(
                        fields=["created_at", "key"], name="ws_summary_created_key_idx"
                    ),
                    GinIndex(
                        fields=["payload"],
                        opclasses=["jsonb_path_ops"],
                        condition=models.Q(channel_group="users"),
                        name="ws_summary_users_payload_idx",
                    ),
                ],
            },
        ),
        migrations.CreateModel(
            name="RealtimeEventHistoryState",
            fields=[
                (
                    "id",
                    models.PositiveSmallIntegerField(
                        db_default=1, primary_key=True, serialize=False
                    ),
                ),
                ("floor", models.BigIntegerField(db_default=0)),
            ],
            options={
                "db_table": "ws_realtime_event_history_state",
                "constraints": [
                    models.CheckConstraint(
                        condition=models.Q(id=1), name="ws_history_state_singleton"
                    ),
                ],
            },
        ),
        migrations.RunPython(forwards, backwards),
    ]
