import sys
import re
from tqdm import tqdm
from pytz import timezone as pytz_timezone
from pytz.exceptions import UnknownTimeZoneError
from tempfile import NamedTemporaryFile

from django.db import transaction
from django.core.management.base import BaseCommand

from baserow.core.models import Group
from baserow.core.utils import Progress
from baserow.contrib.database.airtable.handler import AirtableHandler
from baserow.contrib.database.airtable.exceptions import AirtableBaseNotPublic


class Command(BaseCommand):
    help = (
        "This management command copies all the data from a publicly shared Airtable "
        "base and tries to import a copy into the provided group. A base can be "
        "shared publicly by clicking on the `Share` button in the top right corner and "
        "then create a `Shared base link`. The resulting URL must be provided as "
        "argument."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "group_id",
            type=int,
            help="The group ID where a copy of the imported Airtable base must be "
            "added to.",
        )
        parser.add_argument(
            "public_base_url",
            type=str,
            help="The URL of the publicly shared Airtable base "
            "(e.g. https://airtable.com/shrxxxxxxxxxxxxxx).",
        )
        parser.add_argument(
            "--timezone",
            type=str,
            nargs="?",
            default="UTC",
            help="The default timezone used when formatting dates.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        group_id = options["group_id"]
        public_base_url = options["public_base_url"]

        try:
            timezone = pytz_timezone(options["timezone"])
        except UnknownTimeZoneError:
            self.stdout.write(
                self.style.ERROR(
                    f"The provided timezone {options['timezone']} is " f"unknown."
                )
            )
            sys.exit(1)

        try:
            group = Group.objects.get(pk=group_id)
        except Group.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f"The group with id {group_id} was not found.")
            )
            sys.exit(1)

        result = re.search(r"https:\/\/airtable.com\/shr(.*)$", public_base_url)

        if not result:
            self.stdout.write(
                self.style.ERROR(
                    f"Please provide a valid shared Airtable URL (e.g. "
                    f"https://airtable.com/shrxxxxxxxxxxxxxx)"
                )
            )
            sys.exit(1)

        with tqdm(total=1000) as progress_bar:
            progress = Progress(1000)

            def progress_updated(percentage, state):
                progress_bar.set_description(state)
                progress_bar.update(progress.progress - progress_bar.n)

            progress.register_updated_event(progress_updated)

            share_id = f"shr{result.group(1)}"

            try:
                with NamedTemporaryFile() as download_files_buffer:
                    AirtableHandler.import_from_airtable_to_group(
                        group,
                        share_id,
                        timezone,
                        progress_builder=progress.create_child_builder(
                            represents_progress=progress.total
                        ),
                        download_files_buffer=download_files_buffer,
                    )
            except AirtableBaseNotPublic:
                self.stdout.write(
                    self.style.ERROR(
                        "The Airtable base is not shared publicly. A base can be "
                        "shared publicly by clicking on the `Share` button in the "
                        "top right corner and then create a `Shared base link`."
                    )
                )
                sys.exit(1)

        self.stdout.write(f"Your base has been imported.")
