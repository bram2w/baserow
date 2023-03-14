import os
import sys

from django.core.management.base import BaseCommand

from tqdm import tqdm

from baserow.contrib.database.models import Database
from baserow.contrib.database.table.handler import TableHandler
from baserow.core.management.utils import run_command_concurrently


class Command(BaseCommand):
    help = (
        "Fills a database with many simple tables. Useful for quickly populating "
        "the model cache with a large number of table models."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "database_id", type=int, help="The database to create tables in."
        )
        parser.add_argument(
            "limit",
            nargs="?",
            type=int,
            help="Amount of tables that need to be created.",
            default=0,
        )
        parser.add_argument(
            "concurrency",
            nargs="?",
            type=int,
            help="How many concurrent processes should be used to create tables.",
            default=8,
        )

    def handle(self, *args, **options):
        database_id = options["database_id"]
        limit = options["limit"]
        concurrency = options["concurrency"]

        try:
            database = Database.objects.get(pk=database_id)
        except Database.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f"The database with id {database_id} was not found.")
            )
            sys.exit(1)

        if concurrency == 1:
            fill_database_with_tables(limit, database)
        else:
            run_command_concurrently(
                [
                    "./baserow",
                    "fill_tables",
                    str(database_id),
                    str(int(limit / concurrency)),
                    str(1),
                ],
                concurrency,
            )

        self.stdout.write(self.style.SUCCESS(f"{limit} tables have been created."))


def fill_database_with_tables(limit: int, database: Database):
    process_id = os.getpid()
    print(f"Starting making tables in sub process {process_id}")
    user = database.workspace.users.first()
    for i in tqdm(range(limit), desc=f"Worker {process_id}"):
        TableHandler().create_table(
            user, database, name=f"Table {i} from process {process_id}"
        )
