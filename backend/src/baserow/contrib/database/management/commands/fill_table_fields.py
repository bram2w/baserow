import random
import sys

from django.core.management.base import BaseCommand

from baserow.contrib.database.fields.field_helpers import (
    construct_all_possible_field_kwargs,
)
from baserow.contrib.database.fields.handler import FieldHandler
from baserow.contrib.database.table.models import Table


class Command(BaseCommand):
    help = "Fills a table with random fields."

    def add_arguments(self, parser):
        parser.add_argument(
            "table_id", type=int, help="The table that needs to be filled."
        )
        parser.add_argument(
            "limit",
            nargs="?",
            type=int,
            help="Amount of fields that need to be created.",
            default=0,
        )
        parser.add_argument(
            "--add-all-fields",
            action="store_true",
            help="Add a column for every field type other than link row to the table "
            "before populating it.",
        )

    def handle(self, *args, **options):
        table_id = options["table_id"]
        limit = options["limit"]
        add_all_fields = "add_all_fields" in options and options["add_all_fields"]

        try:
            table = Table.objects.get(pk=table_id)
        except Table.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f"The table with id {table_id} was not found.")
            )
            sys.exit(1)

        fill_table_fields(limit, table)

        if add_all_fields:
            limit += create_field_for_every_type(table)

        self.stdout.write(self.style.SUCCESS(f"{limit} fields have been created."))


def fill_table_fields(limit, table):
    field_handler = FieldHandler()
    all_kwargs_per_type = construct_all_possible_field_kwargs(None, None, None, None)
    first_user = table.database.group.users.first()
    # Keep all fields but link_row and lookup
    allowed_field_list = [
        f for f in all_kwargs_per_type.items() if f[0] not in ["link_row", "lookup"]
    ]
    for _ in range(limit):
        # This is a helper cli command, randomness is not being used for any security
        # or crypto related reasons.
        field_type_name, all_kwargs = random.choice(allowed_field_list)  # nosec
        # These two kwarg types depend on another field existing, which it might
        # not as we are picking randomly.
        allowed_kwargs_list = [
            kwargs
            for kwargs in all_kwargs
            if kwargs["name"] not in ["formula_singleselect", "formula_email"]
        ]
        kwargs = random.choice(allowed_kwargs_list)  # nosec
        kwargs.pop("primary", None)
        kwargs["name"] = field_handler.find_next_unused_field_name(
            table, [kwargs["name"]]
        )
        field_handler.create_field(first_user, table, field_type_name, **kwargs)


def create_field_for_every_type(table):
    field_handler = FieldHandler()
    all_kwargs_per_type = construct_all_possible_field_kwargs(None, None, None, None)
    first_user = table.database.group.users.first()
    i = 0
    for field_type_name, all_possible_kwargs in all_kwargs_per_type.items():
        if field_type_name in ["link_row", "lookup"]:
            continue
        for kwargs in all_possible_kwargs:
            kwargs.pop("primary", None)
            kwargs["name"] = field_handler.find_next_unused_field_name(
                table, [kwargs["name"]]
            )
            field_handler.create_field(first_user, table, field_type_name, **kwargs)
            i += 1
    return i
