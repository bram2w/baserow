# We need to change all NumberFields that are Integers to use DecimalField in Django
# and NUMERIC(50, 0) in Postgres. This migration converts all the existing Integer data
# types in fields to Decimal.
from django.db import connection, migrations

from baserow.contrib.database.fields.models import Field as FieldModel


def alter_sql(schema_editor, table_name, column_name):
    changes_sql = schema_editor.sql_alter_column_type % {
        "column": schema_editor.quote_name(column_name),
        "type": "NUMERIC(50,0)",
    }
    return schema_editor.sql_alter_column % {
        "table": schema_editor.quote_name(table_name),
        "changes": changes_sql,
    }


def forward(apps, schema_editor):
    NumberField = apps.get_model("database", "NumberField")

    with connection.schema_editor(atomic=False) as tables_schema_editor:
        for field in NumberField.objects.filter(number_type="INTEGER"):
            table_name = f"database_table_{field.table.id}"
            column_name = FieldModel.db_column.__get__(field, FieldModel)
            sql = alter_sql(tables_schema_editor, table_name, column_name)
            tables_schema_editor.execute(sql)


class Migration(migrations.Migration):
    atomic = False
    dependencies = [
        ("database", "0022_row_order"),
    ]

    operations = [
        migrations.RunPython(forward, migrations.RunPython.noop),
    ]
