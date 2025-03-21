# Generated by Django 3.2.21 on 2023-09-19 08:11
from django.db import connection, migrations

from baserow.core.psycopg import sql


def remove_duplicates(model, view):
    with connection.cursor() as cursor:
        cursor.execute(
            sql.SQL(
                """
DELETE FROM {table_name}
    WHERE id IN (
        SELECT
            UNNEST(ARRAY_REMOVE(dupe_ids, min_id))
        FROM (
            SELECT
                field_id, {view},
                MIN(t.id) AS min_id,
                ARRAY_AGG(t.id) AS dupe_ids
            FROM
                {table_name} t
            GROUP BY
                field_id, {view}
            HAVING
                COUNT(t.id) > 1
        ) a
    )
    """
            ).format(
                table_name=sql.Identifier(model._meta.db_table),
                view=sql.Identifier(view),
            )
        )


def forward(apps, schema_editor):
    GridViewFieldOptions = apps.get_model("database", "GridViewFieldOptions")
    FormViewFieldOptions = apps.get_model("database", "FormViewFieldOptions")
    GalleryViewFieldOptions = apps.get_model("database", "GalleryViewFieldOptions")

    for ViewFieldOptions, view_fk_field_name in (
        (GridViewFieldOptions, "grid_view_id"),
        (GalleryViewFieldOptions, "gallery_view_id"),
        (FormViewFieldOptions, "form_view_id"),
    ):
        remove_duplicates(ViewFieldOptions, view_fk_field_name)


class Migration(migrations.Migration):
    dependencies = [
        ("database", "0127_viewgroupby"),
    ]

    operations = [
        migrations.RunPython(forward, migrations.RunPython.noop),
    ]
