# Generated by Django 5.0.9 on 2024-11-26 19:49

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("baserow_enterprise", "0034_samlappauthprovidermodel_and_more"),
        ("database", "0173_datasyncsyncedproperty_metadata"),
    ]

    operations = [
        migrations.CreateModel(
            name="HubSpotContactsDataSync",
            fields=[
                (
                    "datasync_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="database.datasync",
                    ),
                ),
                (
                    "hubspot_access_token",
                    models.CharField(
                        help_text="The private app access token used to authenticate requests to HubSpot.",
                        max_length=255,
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
            bases=("database.datasync",),
        ),
    ]
