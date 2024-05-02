from django.core.management.base import BaseCommand

from baserow.core.handler import CoreHandler


class Command(BaseCommand):
    help = (
        "Synchronizes all the templates stored in the database with the JSON files in "
        "the templates directory. This command must be ran every time a template "
        "changes."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "search",
            type=str,
            help="The search pattern to load only some templates.",
        )

    def handle(self, *args, **options):
        search_glob = options["search"]

        if search_glob:
            CoreHandler().sync_templates(template_search_glob=search_glob)
        else:
            CoreHandler().sync_templates()
