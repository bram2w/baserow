# Note that if you have a lot of tables, it might table a while before this migration
# completes.

from django.db import migrations, connection
from django.db.models import F

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
                    columns.column_name = 'order'
            )
        """,
        [f"database_table_{table_id}"],
    )
    rows = cursor.fetchall()
    return rows[0][0]


def add_to_tables(apps, schema_editor):
    Table = apps.get_model("database", "Table")

    cursor = connection.cursor()
    with connection.schema_editor() as tables_schema_editor:
        # We need to stop the transaction because we might need to lock a lot of tables
        # which could result in an out of memory exception.
        tables_schema_editor.atomic.__exit__(None, None, None)

        for table in Table.objects.all():
            if not exists(cursor, table.id):
                to_model = TableModel.get_model(table, field_ids=[])
                order = to_model._meta.get_field("order")
                order.default = "1"
                tables_schema_editor.add_field(to_model, order)
                to_model.objects.all().update(order=F("id"))


def remove_from_tables(apps, schema_editor):
    Table = apps.get_model("database", "Table")

    cursor = connection.cursor()
    with connection.schema_editor() as tables_schema_editor:
        tables_schema_editor.atomic.__exit__(None, None, None)

        for table in Table.objects.all():
            if exists(cursor, table.id):
                to_model = TableModel.get_model(table, field_ids=[])
                order = to_model._meta.get_field("order")
                tables_schema_editor.remove_field(to_model, order)


class Migration(migrations.Migration):

    dependencies = [
        ("database", "0021_auto_20201215_2047"),
    ]

    operations = [migrations.RunPython(add_to_tables, remove_from_tables)]
