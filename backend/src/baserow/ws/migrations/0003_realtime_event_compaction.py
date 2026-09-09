from django.db import migrations, models, transaction

PENDING_INDEX = "ws_realtime_pending_age_idx"
SENTINEL_INDEX = "ws_realtime_sentinel_key_uniq"

INITIALIZE_HISTORY = """
CREATE OR REPLACE FUNCTION ws_initialize_realtime_history() RETURNS void
LANGUAGE plpgsql AS $function$
DECLARE
    event_sequence regclass;
    sequence_value bigint;
    sequence_called boolean;
BEGIN
    -- Called by this migration, RealtimeEventHandler._initialize_realtime_history()
    -- when replay finds no history state, and ws_record_deleted_realtime_history().
    -- Create a conservative boundary: replay cursors below this floor must refresh.
    IF EXISTS (SELECT 1 FROM ws_realtime_event_history_state WHERE id = 1) THEN
        RETURN;
    END IF;
    -- Only initialization takes this lock. Pending INSERTs must finish before
    -- their allocated IDs can become the floor returned to a fresh connection.
    LOCK TABLE ws_realtime_events IN SHARE MODE;
    -- Another initializer may have created the state while we waited for the lock.
    IF EXISTS (SELECT 1 FROM ws_realtime_event_history_state WHERE id = 1) THEN
        RETURN;
    END IF;
    event_sequence := pg_get_serial_sequence('ws_realtime_events', 'id')::regclass;
    -- Cached IDs must not be inserted later below the floor we are about to trust.
    IF NOT EXISTS (
        SELECT 1 FROM pg_sequence WHERE seqrelid = event_sequence AND seqcache = 1
    ) THEN
        RAISE EXCEPTION 'Realtime history requires CACHE 1 for the event sequence';
    END IF;
    -- The logged sequence survives a crash that empties the UNLOGGED tables.
    -- max(event.id) would lose that evidence; an unused sequence instead means 0.
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
    -- Called only by RealtimeEventHandler._compact_realtime_events_batch(), not
    -- on INSERT or replay. Return audience/recovery metadata for grouping old rows.
    -- The caller combines this with channel_group, hashes it for sentinel_key, and
    -- checks exact equality before deleting: a hash collision must not merge routes.
    SELECT jsonb_build_object(
        'type', event_payload->'type',
        'ignore_web_socket_id', event_payload->'ignore_web_socket_id',
        'send_to_all_users', COALESCE(event_payload->'send_to_all_users', 'false'),
        -- Recipient and exclusion lists are sets: order/duplicates change no route.
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
        -- Keep inner event types, including each individual recipient's type:
        -- row-history snapshot recovery differs from events requiring a full refresh.
        -- Business data stays in the retained original row, outside this route key.
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

RECORD_DELETED_HISTORY = """
CREATE OR REPLACE FUNCTION ws_record_deleted_realtime_history() RETURNS trigger
LANGUAGE plpgsql AS $function$
BEGIN
    -- Called once per DELETE statement by ws_realtime_events_history_after_delete.
    -- Its transition table, ws_deleted_realtime_events, contains all deleted rows.
    -- _compact_realtime_events_batch() sets this transaction-local flag only around
    -- deletes with a proven same-route, higher-ID replacement. All other DELETEs
    -- (including legacy cleanup) may lose history and must invalidate older cursors.
    IF current_setting('baserow.realtime_compacting', true) = 'on' THEN
        RETURN NULL;
    END IF;
    PERFORM ws_initialize_realtime_history();
    -- Advance the global floor atomically with the deletion, never moving it back.
    -- A statement deleting no rows leaves it unchanged; the trigger return is ignored.
    UPDATE ws_realtime_event_history_state
    SET floor = greatest(floor, (SELECT max(id) FROM ws_deleted_realtime_events))
    WHERE id = 1 AND EXISTS (SELECT 1 FROM ws_deleted_realtime_events);
    RETURN NULL;
END;
$function$;
"""


def _set_timeouts(cursor):
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


def _create_index(cursor, name, definition, *, unique=False):
    # As in database.0215, recover interrupted concurrent builds on retry.
    cursor.execute(
        "SELECT indisvalid AND indisready FROM pg_index "
        "WHERE indexrelid = to_regclass(%s) "
        "AND indrelid = 'ws_realtime_events'::regclass",
        [name],
    )
    existing = cursor.fetchone()
    if existing is not None and not existing[0]:
        cursor.execute(f'DROP INDEX CONCURRENTLY "{name}"')
    qualifier = "UNIQUE " if unique else ""
    cursor.execute(
        f'CREATE {qualifier}INDEX CONCURRENTLY IF NOT EXISTS "{name}" '
        f"ON ws_realtime_events {definition}"
    )


def forwards(apps, schema_editor):
    """Install compaction helpers and initialize the floor; cleanup compacts later."""

    db = schema_editor.connection
    # Cleanup must be paused/drained until all ASGI and Celery workers use the
    # new reader/retention rules. The parent reader cannot recognize sentinels.
    # Short metadata changes are atomic; the large-table indexes build outside
    # that transaction without blocking normal INSERTs.
    with transaction.atomic(using=db.alias), db.cursor() as cursor:
        _set_timeouts(cursor)
        cursor.execute("LOCK TABLE ws_realtime_events IN SHARE ROW EXCLUSIVE MODE")
        cursor.execute(
            "ALTER TABLE ws_realtime_events ADD COLUMN IF NOT EXISTS sentinel_key bytea DEFAULT NULL"
        )
        cursor.execute(
            "CREATE UNLOGGED TABLE IF NOT EXISTS ws_realtime_event_history_state ("
            "id smallint DEFAULT 1 PRIMARY KEY CHECK (id >= 0), "
            "floor bigint NOT NULL DEFAULT 0, "
            "CONSTRAINT ws_history_state_singleton CHECK (id = 1))"
        )
        cursor.execute("ALTER TABLE ws_realtime_event_history_state SET UNLOGGED")
        # 0001's SET UNLOGGED also changed its owned sequence on PostgreSQL15+.
        # PostgreSQL14 has only logged sequences and no SET LOGGED syntax.
        cursor.execute(
            "DO $block$ DECLARE event_sequence regclass; BEGIN "
            "event_sequence := pg_get_serial_sequence('ws_realtime_events', 'id')::regclass; "
            "IF EXISTS (SELECT 1 FROM pg_class "
            "WHERE oid = event_sequence AND relpersistence <> 'p') THEN "
            "EXECUTE format('ALTER SEQUENCE %s SET LOGGED', event_sequence); "
            "END IF; END $block$"
        )
        cursor.execute(INITIALIZE_HISTORY)
        cursor.execute(ROUTING_PAYLOAD)
        cursor.execute(RECORD_DELETED_HISTORY)
        cursor.execute("SELECT ws_initialize_realtime_history()")
        cursor.execute(
            "DROP TRIGGER IF EXISTS ws_realtime_events_history_after_delete ON ws_realtime_events"
        )
        cursor.execute(
            "CREATE TRIGGER ws_realtime_events_history_after_delete "
            "AFTER DELETE ON ws_realtime_events "
            "REFERENCING OLD TABLE AS ws_deleted_realtime_events "
            "FOR EACH STATEMENT EXECUTE FUNCTION ws_record_deleted_realtime_history()"
        )
    with db.cursor() as cursor:
        _create_index(
            cursor,
            PENDING_INDEX,
            "(created_at, id) WHERE sentinel_key IS NULL",
        )
        _create_index(
            cursor,
            SENTINEL_INDEX,
            "(sentinel_key) WHERE sentinel_key IS NOT NULL",
            unique=True,
        )


def backwards(apps, schema_editor):
    db = schema_editor.connection
    with db.cursor() as cursor:
        cursor.execute(f'DROP INDEX CONCURRENTLY IF EXISTS "{PENDING_INDEX}"')
        cursor.execute(f'DROP INDEX CONCURRENTLY IF EXISTS "{SENTINEL_INDEX}"')
    with transaction.atomic(using=db.alias), db.cursor() as cursor:
        _set_timeouts(cursor)
        cursor.execute("LOCK TABLE ws_realtime_events IN SHARE ROW EXCLUSIVE MODE")
        cursor.execute(
            "DROP TRIGGER IF EXISTS ws_realtime_events_history_after_delete ON ws_realtime_events"
        )
        cursor.execute("DROP FUNCTION IF EXISTS ws_record_deleted_realtime_history()")
        cursor.execute("DROP FUNCTION IF EXISTS ws_realtime_event_routing(jsonb)")
        cursor.execute("DROP FUNCTION IF EXISTS ws_initialize_realtime_history()")
        cursor.execute("DROP TABLE IF EXISTS ws_realtime_event_history_state")
        cursor.execute(
            "ALTER TABLE ws_realtime_events DROP COLUMN IF EXISTS sentinel_key"
        )
        # Preserve original rows and the durable sequence. Before restarting the
        # old reader, rollback must clear/disable replay separately: retained old
        # cursors could otherwise anchor across events already compacted away.


class Migration(migrations.Migration):
    atomic = False
    dependencies = [("ws", "0002_realtime_event_indexes")]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunPython(forwards, backwards, atomic=False)
            ],
            state_operations=[
                migrations.AddField(
                    model_name="realtimeevent",
                    name="sentinel_key",
                    field=models.BinaryField(null=True, db_default=None),
                ),
                migrations.AddIndex(
                    model_name="realtimeevent",
                    index=models.Index(
                        fields=["created_at", "id"],
                        condition=models.Q(sentinel_key__isnull=True),
                        name=PENDING_INDEX,
                    ),
                ),
                migrations.AddConstraint(
                    model_name="realtimeevent",
                    constraint=models.UniqueConstraint(
                        fields=["sentinel_key"],
                        condition=models.Q(sentinel_key__isnull=False),
                        name=SENTINEL_INDEX,
                    ),
                ),
                migrations.CreateModel(
                    name="RealtimeEventHistoryState",
                    fields=[
                        (
                            "id",
                            models.PositiveSmallIntegerField(
                                db_default=1,
                                primary_key=True,
                                serialize=False,
                            ),
                        ),
                        ("floor", models.BigIntegerField(db_default=0)),
                    ],
                    options={
                        "db_table": "ws_realtime_event_history_state",
                        "constraints": [
                            models.CheckConstraint(
                                condition=models.Q(id=1),
                                name="ws_history_state_singleton",
                            )
                        ],
                    },
                ),
            ],
        ),
    ]
