from django.core.management import BaseCommand

from baserow.contrib.database.table.cache import clear_generated_model_cache


class Command(BaseCommand):
    help = "Clears Baserow's internal generated model cache"

    def handle(self, *args, **options):
        clear_generated_model_cache()
