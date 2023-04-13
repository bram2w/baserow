from django.db import migrations


def get_settings(Settings):
    try:
        return Settings.objects.all()[:1].get()
    except Settings.DoesNotExist:
        return Settings.objects.create()


def set_show_admin_signup_page(apps, schema_editor):
    SettingsModel = apps.get_model("core", "Settings")
    settings = get_settings(SettingsModel)
    User = apps.get_model("auth", "User")
    settings.show_admin_signup_page = not User.objects.exists()
    settings.save()


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0026_settings_show_admin_signup_page"),
    ]

    operations = [
        migrations.RunPython(
            set_show_admin_signup_page, reverse_code=migrations.RunPython.noop
        ),
    ]
