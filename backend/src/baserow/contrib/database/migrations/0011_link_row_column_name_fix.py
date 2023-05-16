# There was a bug where if table contained a link row field and the user changes the
# name of the table it would crash. This was because the name of the foreignkey columns
# was related to the name of the table. The name of now based on the id of the table
# which makes it of course more robust. This migration checks all the through tables to
# see if some names are incorrect and if so they will be corrected.

from django.db import connection, migrations


def rename_sql(schema_editor, table, old_name, new_name):
    return schema_editor.sql_rename_column % {
        "table": schema_editor.quote_name(table),
        "old_column": schema_editor.quote_name(old_name),
        "new_column": schema_editor.quote_name(new_name),
        "type": None,
    }


def forward(apps, schema_editor):
    LinkRowField = apps.get_model("database", "LinkRowField")

    cursor = connection.cursor()
    with connection.schema_editor() as tables_schema_editor:
        for field in LinkRowField.objects.all():
            table_name = f"database_relation_{field.link_row_relation_id}"
            new_name = f"table{field.table.id}model_id"
            first = field.id < field.link_row_related_field.id

            cursor.execute(
                "SELECT column_name FROM information_schema.columns WHERE "
                "table_name = %s",
                [table_name],
            )
            rows = cursor.fetchall()

            # Because it is a through table we expect exactly 3 columns, the id,
            # foreignkey 1 and foreignkey 2.
            if len(rows) != 3:
                continue

            # Because the first column is always the first created link row field we
            # which column is related to the field object.
            old_name = rows[1][0] if first else rows[2][0]

            if old_name != new_name:
                tables_schema_editor.execute(
                    rename_sql(tables_schema_editor, table_name, old_name, new_name)
                )


class Migration(migrations.Migration):
    dependencies = [
        ("database", "0010_auto_20200828_1306"),
    ]

    operations = [
        migrations.RunPython(forward, migrations.RunPython.noop),
    ]
