from django.db import migrations
from django.db.models.expressions import RawSQL

PLAIN_COMMENT_TO_TIPTAP_JSON_MIGRATION = """
jsonb_build_object(
    'type', 'doc',
    'content', jsonb_build_array(
        jsonb_build_object(
            'type', 'paragraph',
            'content', jsonb_build_array(
                jsonb_build_object('type', 'text', 'text', comment)
            )
        )
    )
)
"""


def forward(apps, schema_editor):
    RowComment = apps.get_model("baserow_premium", "RowComment")
    RowComment.objects.update(
        message=RawSQL(  # nosec
            PLAIN_COMMENT_TO_TIPTAP_JSON_MIGRATION,
            [],
        )
    )


class Migration(migrations.Migration):
    dependencies = [
        ("baserow_premium", "0011_add_row_comments_message_and_mentions"),
    ]

    operations = [
        migrations.RunPython(forward, migrations.RunPython.noop),
    ]
