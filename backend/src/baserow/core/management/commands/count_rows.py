from django.core.management import BaseCommand

from baserow.contrib.database.table.handler import TableHandler


class Command(BaseCommand):
    help = (
        "Runs the periodic count rows task without having to wait for the time trigger"
    )

    def handle(self, *args, **options):
        TableHandler.count_rows()
