import sys

from django.core.management.base import BaseCommand

from baserow.cachalot_patch import clear_cachalot_cache


class Command(BaseCommand):
    help = "Manually clears the cachalot cache."

    def handle(self, *args, **options):
        try:
            clear_cachalot_cache()
        except Exception as e:
            self.stdout.write(self.style.ERROR(e.message))
            sys.exit(1)
