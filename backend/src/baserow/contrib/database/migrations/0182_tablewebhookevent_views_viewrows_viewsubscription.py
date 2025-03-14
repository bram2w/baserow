# Generated by Django 5.0.9 on 2025-03-07 15:43

import django.contrib.postgres.fields
import django.db.models.deletion
from django.db import migrations, models

import baserow.core.fields


class Migration(migrations.Migration):
    dependencies = [
        ("contenttypes", "0002_remove_content_type_name"),
        ("database", "0181_tablewebhookcall_batch_id_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="tablewebhookevent",
            name="views",
            field=models.ManyToManyField(to="database.view"),
        ),
        migrations.CreateModel(
            name="ViewRows",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_on", models.DateTimeField(auto_now_add=True)),
                ("updated_on", baserow.core.fields.SyncedDateTimeField(auto_now=True)),
                (
                    "row_ids",
                    django.contrib.postgres.fields.ArrayField(
                        base_field=models.PositiveIntegerField(),
                        default=list,
                        help_text="The rows that are shown in the view. This list can be used by webhooks to determine which rows have been changed since the last check.",
                        size=None,
                    ),
                ),
                (
                    "view",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="rows",
                        to="database.view",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="ViewSubscription",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("subscriber_id", models.PositiveIntegerField()),
                (
                    "subscriber_content_type",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="contenttypes.contenttype",
                    ),
                ),
                (
                    "view",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="subscribers",
                        to="database.view",
                    ),
                ),
            ],
            options={
                "unique_together": {
                    ("view", "subscriber_content_type", "subscriber_id")
                },
            },
        ),
    ]
