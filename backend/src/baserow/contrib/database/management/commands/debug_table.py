import json
import traceback

from django.core.management.base import BaseCommand

from baserow.contrib.database.fields.registries import field_type_registry
from baserow.contrib.database.table.models import Table


class Command(BaseCommand):
    help = (
        "Shows the fields of a specific table and all of their properties for "
        "debugging purposes."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "table_id",
            type=int,
            help="The ID of the table to get the fields for.",
        )

    def handle(self, *args, **options):
        table_id = options["table_id"]
        table = Table.objects.get(id=table_id)

        print(f"Table {table.name}({table.id}) has {table.field_set.count()} fields:")
        for field in table.field_set.all():
            # noinspection PyBroadException
            try:
                field = field.specific
                field_type = field_type_registry.get_by_model(field.specific_class)
                print(
                    f"--> Field {field.name}({field.id}) of type {field_type.type} has "
                    f"values:"
                )
                print(json.dumps(field_type.export_serialized(field), indent=4))
            except Exception:
                print(f"Failed to get field values for field {field.id}:")
                traceback.format_exc()
