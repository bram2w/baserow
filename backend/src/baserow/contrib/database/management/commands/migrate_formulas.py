from django.core.management.base import BaseCommand

from baserow.contrib.database.formula.migrations.handler import FormulaMigrationHandler
from baserow.contrib.database.table.cache import clear_generated_model_cache


class Command(BaseCommand):
    help = (
        "Ensures all formulas have been correctly migrated to the current "
        "formula version. This is done automatically when you run the normal migrate "
        "command unless you have set the DONT_UPDATE_FORMULAS_AFTER_MIGRATION variable."
        " This command lets you manually run only the formula migration if you want to"
        " run it separately from the normal database migration for example."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dont-clear-model-cache",
            action="store_true",
            help="By default this command first clears the model cache. If you have"
            " want to disable this provide this flag.",
        )

    def handle(self, *args, **options):
        dont_clear_model_cache = options.get("dont_clear_model_cache", False)

        if not dont_clear_model_cache:
            clear_generated_model_cache()

        FormulaMigrationHandler.migrate_formulas_to_latest_version()
