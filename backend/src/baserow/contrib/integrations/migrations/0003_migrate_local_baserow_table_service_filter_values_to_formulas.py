from django.db import migrations

from baserow.contrib.integrations.migrations.helpers.migrate_local_baserow_table_service_filter_values_to_formulas import (
    reduce_to_filter_types_to_migrate,
)
from baserow.core.formula.parser.parser import convert_string_to_string_literal_token


def forward(apps, schema_editor):
    LocalBaserowTableServiceFilter = apps.get_model(
        "integrations", "LocalBaserowTableServiceFilter"
    )
    updates = []
    service_filters = LocalBaserowTableServiceFilter.objects.all()
    filters_to_migrate = reduce_to_filter_types_to_migrate(service_filters)
    for service_filter in filters_to_migrate:
        service_filter.value = convert_string_to_string_literal_token(
            service_filter.value, True
        )
        updates.append(service_filter)
    LocalBaserowTableServiceFilter.objects.bulk_update(updates, ["value"])


class Migration(migrations.Migration):
    dependencies = [
        ("integrations", "0002_migrate_local_baserow_service_value_to_formulafield"),
    ]

    operations = [
        migrations.RunPython(forward, migrations.RunPython.noop),
    ]
