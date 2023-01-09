from django.apps import apps
from django.conf import settings
from django.core.management import CommandError
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.module_loading import import_string

POPULATE_MODULE_NAME = "populate"
LOAD_TEST_DATA_NAME = "load_test_data"


class Command(BaseCommand):
    help = "Populate test data from installed apps"

    def add_arguments(self, parser):
        parser.add_argument("-d", "--dry-run", action="store_true", help="Dry-run mode")
        parser.add_argument(
            "-m",
            "--modules",
            action="store",
            nargs="?",
            help="Load data for this modules",
        )

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError(
                "This command is not intended to be executed in production."
            )

        sid = transaction.savepoint()

        for app_name, load_data_fn in self.available_modules().items():
            with transaction.atomic():
                self.stdout.write("Loading data for application {}".format(app_name))
                load_data_fn()

        if options.get("dry_run"):
            transaction.savepoint_rollback(sid)

    def available_modules(self):
        available_modules = {}

        for app_name, app_config in apps.app_configs.items():
            try:
                available_modules[app_name] = import_string(
                    "{}.{}.{}".format(
                        app_config.module.__package__,
                        POPULATE_MODULE_NAME,
                        LOAD_TEST_DATA_NAME,
                    )
                )
            except ImportError:
                print(f"Application {app_name} has no populate module")

        return available_modules
