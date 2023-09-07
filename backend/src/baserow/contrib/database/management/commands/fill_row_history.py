import itertools
import sys
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from faker import Faker
from tqdm import tqdm

from baserow.contrib.database.rows.actions import UpdateRowsActionType
from baserow.contrib.database.rows.models import RowHistory
from baserow.contrib.database.table.models import Table
from baserow.core.models import WorkspaceUser


class Command(BaseCommand):
    help = "Fills a row history with random changes."

    def add_arguments(self, parser):
        parser.add_argument(
            "table_id", type=int, help="The table that contains the row."
        )
        parser.add_argument(
            "row_id", type=int, help="The row id for which to generate history entries."
        )
        parser.add_argument(
            "--limit",
            type=int,
            help="The number of history entries to generate.",
            default=20,
        )
        parser.add_argument(
            "--clean",
            action="store_true",
            help="If provided, will remove previous entries for the row.",
        )
        parser.add_argument(
            "--randomize-timestamps",
            action="store_true",
            help="If true, will create entries with various timestamps.",
        )

    def handle(self, *args, **options):
        table_id = options["table_id"]
        row_id = options["row_id"]
        limit = options["limit"]
        clean = options.get("clean", False)
        randomize_timestamps = options.get("randomize-timestamps", True)

        try:
            table = Table.objects.get(pk=table_id)
        except Table.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f"The table with id {table_id} was not found.")
            )
            sys.exit(1)

        model = table.get_model()

        try:
            row = model.objects.get(pk=row_id)
        except model.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(
                    f"The row with id {row_id} was not found in table {table_id}."
                )
            )
            sys.exit(1)

        workspace = table.database.workspace
        workspace_users = WorkspaceUser.objects.filter(workspace=workspace)
        wk_admin = workspace_users.filter(permissions="ADMIN").first()

        if clean:
            RowHistory.objects.filter(row_id=row.id, table=table).delete()
            self.stdout.write(self.style.SUCCESS(f"History cleared."))

        with transaction.atomic():
            with tqdm(
                total=limit,
                desc=f"Adding {limit} entries to row history for row {row_id}",
            ) as progress:
                for _ in range(limit):
                    record_row_history(table, row, user=wk_admin.user)
                    progress.update(1)

        if randomize_timestamps:
            overwrite_timestamps(table, row, limit)

        self.stdout.write(self.style.SUCCESS(f"History recorded successfully."))


def record_row_history(table, row, user):
    model = table.get_model()
    fake = Faker()
    cache = {}
    row_random_values = {}
    row_random_values["id"] = row.id

    for _, field_object in model._field_objects.items():
        random_value = field_object["type"].random_value(
            field_object["field"], fake, cache
        )
        row_random_values[f"field_{field_object['field'].id}"] = random_value

    rows_values = [row_random_values]
    UpdateRowsActionType.do(user, table, rows_values, model)


def overwrite_timestamps(table, row, limit):
    now = timezone.now()
    day_ago = now - timedelta(days=1)
    two_days_ago = now - timedelta(days=2)
    three_days_ago = now - timedelta(days=3)
    unique_timestamps = [now, day_ago, two_days_ago, three_days_ago]
    timestamps = list(
        itertools.chain.from_iterable(itertools.repeat(x, 3) for x in unique_timestamps)
    )
    entries = RowHistory.objects.filter(row_id=row.id, table=table).all()[:limit]

    for entry in entries:
        entry.action_timestamp = (
            timestamps.pop(0) if len(timestamps) > 0 else three_days_ago
        )

    RowHistory.objects.bulk_update(entries, ["action_timestamp"])
