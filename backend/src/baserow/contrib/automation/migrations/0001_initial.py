# Generated by Django 5.0.9 on 2025-02-26 20:29

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("core", "0094_alter_importexportresource_size"),
    ]

    operations = [
        migrations.CreateModel(
            name="Automation",
            fields=[
                (
                    "application_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="core.application",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
            bases=("core.application",),
        ),
    ]
