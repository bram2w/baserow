# Note that if you have a lot of tables, it might table a while before this migrations
# completes.

import django.utils.timezone
from django.db import connection, migrations, models

from baserow.contrib.database.table.models import Table as TableModel


def exists(cursor, table_id):
    cursor.execute(
        """
            SELECT exists(
                SELECT
                    1
                FROM
                    information_schema.columns
                WHERE
                    columns.table_name = %s AND
                    columns.column_name = 'created_on'
            )
        """,
        [f"database_table_{table_id}"],
    )
    rows = cursor.fetchall()
    return rows[0][0]


def add_to_tables(apps, schema_editor):
    Table = apps.get_model("database", "Table")

    cursor = connection.cursor()
    with connection.schema_editor(atomic=False) as tables_schema_editor:
        # We need to stop the transaction because we might need to lock a lot of tables
        # which could result in an out of memory exception.

        for table in Table.objects.all():
            if not exists(cursor, table.id):
                to_model = TableModel.get_model(table, field_ids=[])
                created_on = to_model._meta.get_field("created_on")
                updated_on = to_model._meta.get_field("updated_on")
                tables_schema_editor.add_field(to_model, created_on)
                tables_schema_editor.add_field(to_model, updated_on)


def remove_from_tables(apps, schema_editor):
    Table = apps.get_model("database", "Table")

    cursor = connection.cursor()
    with connection.schema_editor(atomic=False) as tables_schema_editor:
        for table in Table.objects.all():
            if exists(cursor, table.id):
                to_model = TableModel.get_model(table, field_ids=[])
                created_on = to_model._meta.get_field("created_on")
                updated_on = to_model._meta.get_field("updated_on")
                tables_schema_editor.remove_field(to_model, created_on)
                tables_schema_editor.remove_field(to_model, updated_on)


class Migration(migrations.Migration):
    atomic = False
    dependencies = [
        ("database", "0020_fix_primary_link_row"),
    ]

    operations = [
        migrations.AddField(
            model_name="field",
            name="created_on",
            field=models.DateTimeField(
                auto_now_add=True, default=django.utils.timezone.now
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="field",
            name="updated_on",
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name="table",
            name="created_on",
            field=models.DateTimeField(
                auto_now_add=True, default=django.utils.timezone.now
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="table",
            name="updated_on",
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name="view",
            name="created_on",
            field=models.DateTimeField(
                auto_now_add=True, default=django.utils.timezone.now
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="view",
            name="updated_on",
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.RunPython(add_to_tables, remove_from_tables),
    ]
