import sys

from django.core.management.base import BaseCommand

from baserow.contrib.database.search.exceptions import (
    PostgresFullTextSearchDisabledException,
)
from baserow.contrib.database.search.handler import SearchHandler
from baserow.contrib.database.table.models import Table


class Command(BaseCommand):
    help = (
        "Given a table ID, this command will update its `tsvector` columns with"
        "the contents of all fields in your table so that it can be searched upon."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "table_id",
            type=int,
            help="The ID of the table to update.",
        )

    def handle(self, *args, **options):
        table_id = options["table_id"]
        try:
            table = Table.objects.get(id=options["table_id"])
        except Table.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f"The table with id {table_id} was not found.")
            )
            sys.exit(1)
        try:
            SearchHandler.update_tsvector_columns(
                table, update_tsvectors_for_changed_rows_only=False
            )
            self.stdout.write(
                self.style.SUCCESS("The tsvector columns were been updated.")
            )
        except PostgresFullTextSearchDisabledException:
            self.stdout.write(
                self.style.ERROR(
                    "Your Baserow installation has Postgres full-text"
                    "search disabled. To use full-text, ensure that"
                    "BASEROW_USE_PG_FULLTEXT_SEARCH=true."
                )
            )
