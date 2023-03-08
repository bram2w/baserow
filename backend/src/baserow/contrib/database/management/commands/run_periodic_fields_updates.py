from django.core.management.base import BaseCommand
from django.db import transaction

from baserow.contrib.database.fields.tasks import run_periodic_fields_updates


class Command(BaseCommand):
    help = "Manually runs the periodic update job for fields"

    def add_arguments(self, parser):
        parser.add_argument(
            "--group_id",
            nargs="?",
            type=int,
            help="The group in which formulas will be updated. If the value is 0, then all groups will be updated",
            default=None,
        )
        parser.add_argument(
            "--dont-update-now",
            action="store_true",
            help="If set to true all the groups will be updated with the current time otherwise the previous `now` value will be used.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        run_periodic_fields_updates(options["group_id"], not options["dont_update_now"])
