import sys
import json
import os

from django.core.management.base import BaseCommand

from baserow.core.models import Group
from baserow.core.handler import CoreHandler


class Command(BaseCommand):
    help = (
        "Exports all the application of a group to a JSON file that can later be "
        "imported via the `import_group_applications` management command. A ZIP file "
        "containing all the files is also exported, this will for example contain the "
        "files uploaded to a file field."
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
        parser.add_argument(
            "--name",
            type=str,
            help="The JSON and ZIP files are going to be named `group_ID.json` and "
            "`group_ID.zip` by default, but can optionally be named differently by "
            "proving this argument.",
        )

    def handle(self, *args, **options):
        group_id = options["group_id"]
        indent = options["indent"]
        name = options["name"]

        try:
            group = Group.objects.get(pk=group_id)
        except Group.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f"The group with id {group_id} was not " f"found.")
            )
            sys.exit(1)

        file_name = name or f"group_{group.id}"
        current_path = os.path.abspath(os.getcwd())
        files_path = os.path.join(current_path, f"{file_name}.zip")
        export_path = os.path.join(current_path, f"{file_name}.json")

        with open(files_path, "wb") as files_buffer:
            exported_applications = CoreHandler().export_group_applications(
                group, files_buffer=files_buffer
            )

        with open(export_path, "w") as export_buffer:
            json.dump(
                exported_applications, export_buffer, indent=4 if indent else None
            )
