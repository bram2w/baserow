from django.core.management.base import BaseCommand

from tqdm import tqdm

from baserow.core.usage.handler import UsageHandler
from baserow.core.utils import Progress


class Command(BaseCommand):
    help = "Calculate the storage usage of every workspace"

    def handle(self, *args, **options):
        progress_total = 1000

        def create_progress_and_update_bar(progress_bar):
            progress = Progress(progress_total)

            def progress_updated(percentage, state=None):
                if state:
                    progress_bar.set_description(state)
                progress_bar.update(progress.progress - progress_bar.n)

            progress.register_updated_event(progress_updated)
            return progress.create_child_builder(represents_progress=progress_total)

        with tqdm(total=progress_total) as progress_bar:
            workspaces_updated = UsageHandler.calculate_storage_usage(
                progress_builder=create_progress_and_update_bar(progress_bar)
            )

        self.stdout.write(
            self.style.SUCCESS(f"{workspaces_updated} workspace(s) have been updated.")
        )
