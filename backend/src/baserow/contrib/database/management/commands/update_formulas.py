from django.core.management.base import BaseCommand

from baserow.contrib.database.formula import FormulaHandler


class Command(BaseCommand):
    help = (
        "Ensures all formulas have been correctly calculated for the current "
        "formula version."
    )

    def handle(self, *args, **options):
        FormulaHandler.recalculate_formulas_according_to_version()
