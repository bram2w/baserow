# Generated by Django 3.2.18 on 2023-06-13 15:36

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("core", "0069_synced_datetime_field"),
    ]

    operations = [
        migrations.AddField(
            model_name="trashentry",
            name="trash_item_owner",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="private_trash_entries",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]