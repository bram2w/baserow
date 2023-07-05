import sys

from django.db import transaction

from tqdm import tqdm

from baserow.contrib.database.models import Database
from baserow.core.management.commands.base_confirmation import BaseConfirmationCommand
from baserow.core.trash.handler import TrashHandler


class Command(BaseConfirmationCommand):
    help = (
        "Given a database ID, this command will permanently delete all tables by iterating "
        "over each table and deleting them outside of a transaction."
    )

    def get_confirmation_message(self, options: dict) -> str:
        try:
            database = Database.objects_and_trash.get(pk=options["database_id"])
        except Database.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(
                    f"The database with id {options['database_id']} was not found."
                )
            )
            sys.exit(1)
        return (
            f'This command will permanently delete {database.table_set.count()} tables in database "{database.name}". '
            f"If you are happy to proceed, run this command again with --confirm."
        )

    def add_arguments(self, parser):
        parser.add_argument(
            "database_id", type=int, help="The database to create tables in."
        )
        super().add_arguments(parser)

    def handle(self, *args, **options):
        super().handle(*args, **options)

        database_id = options["database_id"]
        try:
            database = Database.objects_and_trash.get(pk=database_id)
        except Database.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f"The database with id {database_id} was not found.")
            )
            sys.exit(1)

        tables = database.table_set.all()
        if len(tables) == 0:
            self.stdout.write(
                self.style.ERROR(f"The database with id {database_id} has no tables.")
            )
            sys.exit(1)

        for table in tqdm(
            tables, desc=f"Deleting {len(tables)} tables in database {database.name}."
        ):
            with transaction.atomic():
                TrashHandler.permanently_delete(table)
        self.stdout.write(self.style.SUCCESS("Deletion has completed."))
