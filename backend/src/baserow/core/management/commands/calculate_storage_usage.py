from django.core.management.base import BaseCommand

from baserow.core.usage.handler import UsageHandler


class Command(BaseCommand):
    help = "Calculate the storage usage of every group"

    def handle(self, *args, **options):
        UsageHandler.calculate_storage_usage()
