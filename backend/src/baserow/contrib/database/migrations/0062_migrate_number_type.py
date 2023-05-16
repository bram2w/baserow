from django.db import migrations


def forward(apps, schema_editor):
    """
    If the NumberField.number_type was decimal we keep the decimal places
    intact.

    If the NumberField.number_type was integer we set the decimal places to
    0 as the number field could have any number of decimal places set before.
    """

    NumberField = apps.get_model("database", "NumberField")
    NumberField.objects.filter(number_type="INTEGER").update(number_decimal_places=0)


def reverse(apps, schema_editor):
    ...


class Migration(migrations.Migration):
    dependencies = [
        ("database", "0061_change_decimal_places"),
    ]

    operations = [
        migrations.RunPython(forward, reverse),
    ]
