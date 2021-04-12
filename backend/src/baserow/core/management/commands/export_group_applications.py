import sys
import json

from django.core.management.base import BaseCommand

from baserow.core.models import Group
from baserow.core.handler import CoreHandler


class Command(BaseCommand):
    help = (
        "Exports all the application of a group to a JSON file that can later be "
        "imported via the `import_group_applications` management command. This export "
        "can also be used as a template."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "group_id", type=int, help="The id of the group that must be exported."
        )
        parser.add_argument(
            "--indent",
            action="store_true",
            help="Indicates if the JSON must be formatted and indented to improve "
            "readability.",
        )

    def handle(self, *args, **options):
        group_id = options["group_id"]
        indent = options["indent"]

        try:
            group = Group.objects.get(pk=group_id)
        except Group.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f"The group with id {group_id} was not " f"found.")
            )
            sys.exit(1)

        exported_applications = CoreHandler().export_group_applications(group)
        exported_json = json.dumps(exported_applications, indent=4 if indent else None)
        self.stdout.write(exported_json)
