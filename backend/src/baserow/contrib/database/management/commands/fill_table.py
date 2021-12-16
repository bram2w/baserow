import sys
from collections import defaultdict
from decimal import Decimal
from math import ceil

from django.core.management.base import BaseCommand
from django.db.models import Max
from django.db.models.fields.related import ForeignKey
from faker import Faker

from baserow.contrib.database.fields.field_helpers import (
    construct_all_possible_field_kwargs,
)
from baserow.contrib.database.fields.handler import FieldHandler
from baserow.contrib.database.rows.handler import RowHandler
from baserow.contrib.database.table.models import Table


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
        add_columns = "add_columns" in options and options["add_columns"]

        try:
            table = Table.objects.get(pk=table_id)
        except Table.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f"The table with id {table_id} was not " f"found.")
            )
            sys.exit(1)

        fill_table(limit, table, add_columns=add_columns)

        self.stdout.write(self.style.SUCCESS(f"{limit} rows have been inserted."))


def fill_table(limit, table, add_columns=False):
    fake = Faker()
    row_handler = RowHandler()
    cache = {}
    if add_columns:
        create_a_column_for_every_type(table)
    model = table.get_model()
    # Find out what the highest order is because we want to append the new rows.
    order = ceil(model.objects.aggregate(max=Max("order")).get("max") or Decimal("0"))

    rows = []
    for i in range(0, limit):
        # Based on the random_value function we have for each type we can
        # build a dict with a random value for each field.
        values = {
            f"field_{field_id}": field_object["type"].random_value(
                field_object["field"], fake, cache
            )
            for field_id, field_object in model._field_objects.items()
        }

        values, manytomany_values = row_handler.extract_manytomany_values(values, model)
        order += Decimal("1")
        values["order"] = order

        # Prepare an array of objects that can later be inserted all at once.
        instance = model(**values)
        relations = {
            field_name: value
            for field_name, value in manytomany_values.items()
            if value and len(value) > 0
        }
        rows.append((instance, relations))

    # First create the rows in bulk because that's more efficient than creating them
    # one by one.
    model.objects.bulk_create([row for (row, relations) in rows])

    # Construct an object where the key is the field name of the many to many field
    # that must be populated. The value contains the objects that must be inserted in
    # bulk.
    many_to_many = defaultdict(list)
    for (row, relations) in rows:
        for field_name, value in relations.items():
            through = getattr(model, field_name).through
            through_fields = through._meta.get_fields()
            value_column = None
            row_column = None

            # Figure out which field in the many to many through table holds the row
            # value and which on contains the value.
            for field in through_fields:
                if type(field) is not ForeignKey:
                    continue

                if field.remote_field.model == model:
                    row_column = field.get_attname_column()[1]
                else:
                    value_column = field.get_attname_column()[1]

            for i in value:
                many_to_many[field_name].append(
                    getattr(model, field_name).through(
                        **{
                            row_column: row.id,
                            value_column: i,
                        }
                    )
                )

    for field_name, values in many_to_many.items():
        through = getattr(model, field_name).through
        through.objects.bulk_create(values)


def create_a_column_for_every_type(table):
    field_handler = FieldHandler()
    all_kwargs_per_type = construct_all_possible_field_kwargs(None, None, None)
    for field_type_name, all_possible_kwargs in all_kwargs_per_type.items():
        if field_type_name in ["link_row", "lookup"]:
            continue
        i = 0
        for kwargs in all_possible_kwargs:
            kwargs.pop("primary", None)
            i = i + 1
            field_handler.create_field(
                table.database.group.users.first(), table, field_type_name, **kwargs
            )
