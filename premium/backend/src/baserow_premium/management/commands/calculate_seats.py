from django.core.management.base import BaseCommand

from baserow_premium.usage.handler import PremiumUsageHandler


class Command(BaseCommand):
    help = "Calculate the amount of seats taken per group"

    def handle(self, *args, **options):
        groups_updated = PremiumUsageHandler.calculate_per_group_seats_taken()
        self.stdout.write(
            self.style.SUCCESS(f"{groups_updated} group(s) have been updated.")
        )
