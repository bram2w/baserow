import sys

from django.core.management.base import BaseCommand

from tqdm import tqdm

from baserow.contrib.database.models import Database
from baserow.contrib.database.table.models import Table
from baserow.contrib.database.views.handler import ViewIndexingHandler
from baserow.contrib.database.views.models import View
from baserow.core.models import Workspace


class Command(BaseCommand):
    help = (
        "Create or update indexes for views. Providing a table_id, a database_id or a workspace_id "
        "will update all the indexes of the views of the table, database or workspace."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--view_id",
            nargs="?",
            type=int,
            help=(
                "The view in which the index will be updated. "
                "If the value is None, the table_id, the database_id or workspace_id argument is required."
            ),
            default=None,
        )
        parser.add_argument(
            "--table_id",
            nargs="?",
            type=int,
            help=(
                "The table in which the indexes will be updated. "
                "If the value is None, the view_id, the database_id or the workspace_id argument is required."
            ),
            default=None,
        )
        parser.add_argument(
            "--database_id",
            nargs="?",
            type=int,
            help=(
                "The database in which all the tables indexes will be updated. "
                "If the value is None, the view_id, the table_id or the workspace_id argument is required."
            ),
            default=None,
        )
        parser.add_argument(
            "--workspace_id",
            nargs="?",
            type=int,
            help=(
                "The workspace in which all the tables indexes of all the databases will be updated. "
                "If the value is None, the view_id, the table_id or the database_id argument is required."
            ),
            default=None,
        )

    def handle(self, *args, **options):
        view_id = options["view_id"]
        table_id = options["table_id"]
        database_id = options["database_id"]
        workspace_id = options["workspace_id"]

        if view_id:
            try:
                views = [View.objects.get(pk=view_id)]
            except View.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f"The view with id {view_id} was not found.")
                )
                sys.exit(1)
        elif table_id:
            try:
                views = View.objects.filter(table=Table.objects.get(pk=table_id))
            except Table.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f"The table with id {table_id} was not found.")
                )
                sys.exit(1)
        elif database_id:
            try:
                views = View.objects.filter(
                    table__database=Database.objects.get(pk=database_id)
                )
            except Database.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(
                        f"The database with id {database_id} was not found."
                    )
                )
                sys.exit(1)
        elif workspace_id:
            try:
                views = View.objects.filter(
                    table__database__workspace=Workspace.objects.get(pk=workspace_id)
                )
            except Workspace.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(
                        f"The workspace with id {workspace_id} was not found."
                    )
                )
                sys.exit(1)
        else:
            self.stdout.write(
                self.style.ERROR(
                    "A view_id, a table_id, a database_id or a workspace_id is required."
                )
            )
            sys.exit(1)

        for view in tqdm(views, desc="Updating per view indexes", unit="view"):
            print(
                f"Updating index for view '{view.name}' ({view.pk}) in table '{view.table.name}' ({view.table.pk})"
            )
            ViewIndexingHandler.update_index(view)

        self.stdout.write(
            self.style.SUCCESS(f"Successfully updated indexes for {len(views)} views.")
        )
