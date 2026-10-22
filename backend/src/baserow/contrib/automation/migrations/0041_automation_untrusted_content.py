from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("automation", "0040_automationnode_max_retries_automationnode_on_failure_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="automation",
            name="untrusted_content",
            field=models.BooleanField(
                default=False,
                db_default=False,
                help_text="Blocks custom code nodes until explicitly trusted.",
            ),
        ),
    ]
