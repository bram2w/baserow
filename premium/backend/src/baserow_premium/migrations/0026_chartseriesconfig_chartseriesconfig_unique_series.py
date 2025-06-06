# Generated by Django 5.0.13 on 2025-05-20 04:56

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        (
            "baserow_premium",
            "0025_chartwidget_localbaserowgroupedaggregaterows_and_more",
        ),
    ]

    operations = [
        migrations.CreateModel(
            name="ChartSeriesConfig",
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
                (
                    "series_chart_type",
                    models.CharField(
                        choices=[("BAR", "Bar"), ("LINE", "Line")],
                        default="BAR",
                        help_text="Type of chart to display (Bar or Line).",
                        max_length=4,
                    ),
                ),
                (
                    "series",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="baserow_premium.localbaserowtableserviceaggregationseries",
                    ),
                ),
                (
                    "widget",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="series_config",
                        to="baserow_premium.chartwidget",
                    ),
                ),
            ],
        ),
        migrations.AddConstraint(
            model_name="chartseriesconfig",
            constraint=models.UniqueConstraint(
                fields=("series",), name="unique_series"
            ),
        ),
    ]
