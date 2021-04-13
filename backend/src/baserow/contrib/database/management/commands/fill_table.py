import sys
from math import ceil
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db.models import Max

from faker import Faker

from baserow.contrib.database.fields.field_helpers import (
    construct_all_possible_field_kwargs,
)
from baserow.contrib.database.fields.handler import FieldHandler
from baserow.contrib.database.table.models import Table
from baserow.contrib.database.rows.handler import RowHandler


class Command(BaseCommand):
    help = "Fills a table with random data."

    def add_arguments(self, parser):
        parser.add_argument(
            "table_id", type=int, help="The table that needs to be " "filled."
        )
        parser.add_argument(
            "limit", type=int, help="Amount of rows that need to be " "inserted."
        )
        parser.add_argument(
            "--add-columns",
            action="store_true",
            help="Add a column for every field type other than link row to the table "
            "before populating it.",
        )

    def handle(self, *args, **options):
        table_id = options["table_id"]
        limit = options["limit"]
        fake = Faker()
        row_handler = RowHandler()
        cache = {}

        try:
            table = Table.objects.get(pk=table_id)
        except Table.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f"The table with id {table_id} was not " f"found.")
            )
            sys.exit(1)

        if "add_columns" in options and options["add_columns"]:
            self.create_a_column_for_every_type(table)

        model = table.get_model()

        # Find out what the highest order is because we want to append the new rows.
        order = ceil(
            model.objects.aggregate(max=Max("order")).get("max") or Decimal("0")
        )

        for i in range(0, limit):
            # Based on the random_value function we have for each type we can
            # build a dict with a random value for each field.
            values = {
                f"field_{field_id}": field_object["type"].random_value(
                    field_object["field"], fake, cache
                )
                for field_id, field_object in model._field_objects.items()
            }

            values, manytomany_values = row_handler.extract_manytomany_values(
                values, model
            )
            order += Decimal("1")
            values["order"] = order

            # Insert the row with the randomly created values.
            instance = model.objects.create(**values)

            # Changes the set of the manytomany values.
            for field_name, value in manytomany_values.items():
                if value and len(value) > 0:
                    getattr(instance, field_name).set(value)

        self.stdout.write(self.style.SUCCESS(f"{limit} rows have been inserted."))

    @staticmethod
    def create_a_column_for_every_type(table):
        field_handler = FieldHandler()
        all_kwargs_per_type = construct_all_possible_field_kwargs(None)
        for field_type_name, all_possible_kwargs in all_kwargs_per_type.items():
            if field_type_name == "link_row":
                continue
            i = 0
            for kwargs in all_possible_kwargs:
                i = i + 1
                postfix = str(i) if len(all_possible_kwargs) > 1 else ""
                kwargs["name"] = field_type_name + postfix
                field_handler.create_field(
                    table.database.group.users.first(), table, field_type_name, **kwargs
                )
