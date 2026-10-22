from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("builder", "0081_choiceelement_show_search")]

    operations = [
        migrations.AddField(
            model_name="builder",
            name="untrusted_content",
            field=models.BooleanField(
                default=False,
                db_default=False,
                help_text="Blocks custom code and embedded content until explicitly trusted.",
            ),
        ),
    ]
