from django.core.management.base import BaseCommand

from baserow_premium.usage.handler import PremiumUsageHandler


class Command(BaseCommand):
    help = "Calculate the amount of seats taken per group"

    def handle(self, *args, **options):
        workspaces_updated = PremiumUsageHandler.calculate_per_workspace_seats_taken()
        self.stdout.write(
            self.style.SUCCESS(f"{workspaces_updated} workspaces(s) have been updated.")
        )
