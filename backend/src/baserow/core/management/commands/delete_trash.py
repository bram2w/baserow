from django.core.management.base import BaseCommand

from baserow.core.trash.handler import TrashHandler


class Command(BaseCommand):
    help = "Deletes items from trash that had been marked to be permanently deleted"

    def handle(self, *args, **options):
        TrashHandler().permanently_delete_marked_trash()
