from django.core.management.base import BaseCommand

from baserow.core.usage.handler import UsageHandler


class Command(BaseCommand):
    help = "Calculate the storage usage of every group"

    def handle(self, *args, **options):
        groups_updated = UsageHandler.calculate_storage_usage()
        self.stdout.write(
            self.style.SUCCESS(f"{groups_updated} group(s) have been updated.")
        )
