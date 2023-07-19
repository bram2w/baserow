from django.core.management.base import BaseCommand

from baserow.core.usage.handler import UsageHandler


class Command(BaseCommand):
    help = "Calculate the storage usage of every workspace"

    def handle(self, *args, **options):
        workspaces_updated = UsageHandler.calculate_storage_usage()
        self.stdout.write(
            self.style.SUCCESS(f"{workspaces_updated} workspace(s) have been updated.")
        )
