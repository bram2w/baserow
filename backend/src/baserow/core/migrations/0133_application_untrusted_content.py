from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("core", "0132_createusertemplatejob")]

    operations = [
        migrations.AddField(
            model_name="application",
            name="untrusted_content",
            field=models.BooleanField(
                default=False,
                db_default=False,
                help_text="Blocks custom code and embedded content until explicitly trusted.",
            ),
        ),
    ]
