from django.contrib.postgres.indexes import GinIndex
from django.db import migrations, models

TABLE = "ws_realtime_events"
OLD_INDEX = "ws_realtime_payload_gin_idx"
USERS_INDEX = "ws_realtime_users_payload_idx"
CREATED_INDEX = "ws_realtime_created_id_idx"


def _create_index(cursor, name, definition):
    # Follow database migration 0215: interrupted concurrent builds can leave an
    # invalid index which IF NOT EXISTS would otherwise silently preserve.
    cursor.execute(
        "SELECT indisvalid AND indisready FROM pg_index "
        "WHERE indexrelid = to_regclass(%s) AND indrelid = to_regclass(%s)",
        [name, TABLE],
    )
    existing = cursor.fetchone()
    if existing is not None and not existing[0]:
        cursor.execute(f'DROP INDEX CONCURRENTLY "{name}"')
    cursor.execute(
        f'CREATE INDEX CONCURRENTLY IF NOT EXISTS "{name}" ON "{TABLE}" {definition}'
    )


def forwards(apps, schema_editor):
    with schema_editor.connection.cursor() as cursor:
        _create_index(
            cursor,
            USERS_INDEX,
            "USING gin (payload jsonb_path_ops) WHERE channel_group = 'users'",
        )
        _create_index(cursor, CREATED_INDEX, "(created_at, id)")
        # Match database.0209's high-churn pending-search table settings. Analyze
        # refreshes planner statistics; vacuum reclaims space for deleted events.
        cursor.execute(
            f"""
            ALTER TABLE "{TABLE}" SET (
                autovacuum_analyze_threshold = 2000,
                autovacuum_analyze_scale_factor = 0.002,
                autovacuum_vacuum_threshold = 5000,
                autovacuum_vacuum_scale_factor = 0.01,
                autovacuum_vacuum_insert_threshold = 5000,
                autovacuum_vacuum_insert_scale_factor = 0.01
            )
            """
        )
        # Leave the existing read path in place until both builds have succeeded.
        cursor.execute(f'DROP INDEX CONCURRENTLY IF EXISTS "{OLD_INDEX}"')


def backwards(apps, schema_editor):
    with schema_editor.connection.cursor() as cursor:
        _create_index(cursor, OLD_INDEX, "USING gin (payload jsonb_path_ops)")
        cursor.execute(f'DROP INDEX CONCURRENTLY IF EXISTS "{CREATED_INDEX}"')
        cursor.execute(f'DROP INDEX CONCURRENTLY IF EXISTS "{USERS_INDEX}"')
        cursor.execute(
            f"""
            ALTER TABLE "{TABLE}" RESET (
                autovacuum_analyze_threshold,
                autovacuum_analyze_scale_factor,
                autovacuum_vacuum_threshold,
                autovacuum_vacuum_scale_factor,
                autovacuum_vacuum_insert_threshold,
                autovacuum_vacuum_insert_scale_factor
            )
            """
        )


class Migration(migrations.Migration):
    atomic = False

    dependencies = [("ws", "0001_initial")]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunPython(forwards, backwards, atomic=False),
            ],
            state_operations=[
                migrations.AddIndex(
                    model_name="realtimeevent",
                    index=GinIndex(
                        fields=["payload"],
                        opclasses=["jsonb_path_ops"],
                        condition=models.Q(channel_group="users"),
                        name=USERS_INDEX,
                    ),
                ),
                migrations.AddIndex(
                    model_name="realtimeevent",
                    index=models.Index(fields=["created_at", "id"], name=CREATED_INDEX),
                ),
                migrations.RemoveIndex(model_name="realtimeevent", name=OLD_INDEX),
            ],
        ),
    ]
