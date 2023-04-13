from uuid import uuid4

from django.db import migrations

from baserow.core.utils import grouper


def forward(apps, schema_editor):
    ViewDecoration = apps.get_model("database", "ViewDecoration")
    chunk_size = 1000
    queryset = (
        ViewDecoration.objects.filter(value_provider_conf__colors__isnull=False)
        .only("id", "value_provider_conf")
        .iterator(chunk_size=chunk_size)
    )
    for view_decorations in grouper(chunk_size, queryset):
        for view_decoration in view_decorations:
            for color in view_decoration.value_provider_conf["colors"]:
                color["id"] = str(uuid4())
        ViewDecoration.objects.bulk_update(view_decorations, ["value_provider_conf"])


class Migration(migrations.Migration):
    dependencies = [
        ("database", "0067_viewdecoration"),
        ("baserow_premium", "0006_license_cached_untrusted_instance_wide"),
    ]

    operations = [
        migrations.RunPython(forward, migrations.RunPython.noop),
    ]
