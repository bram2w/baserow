from django.db import transaction
from django.core.management.base import BaseCommand

from baserow.core.handler import CoreHandler


class Command(BaseCommand):
    help = (
        'Synchronizes all the templates stored in the database with the JSON files in '
        'the templates directory. This command must be ran everytime a template '
        'changes.'
    )

    @transaction.atomic
    def handle(self, *args, **options):
        CoreHandler().sync_templates()
