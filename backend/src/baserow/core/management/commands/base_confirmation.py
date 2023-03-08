from django.core.management.base import BaseCommand, CommandError


class BaseConfirmationCommand(BaseCommand):
    def get_confirmation_message(self, options: dict) -> str:
        return "To execute this command against your installation of Baserow, run it again with --confirm."

    def add_arguments(self, parser):
        parser.add_argument(
            "--confirm",
            action="store_true",
            default=False,
            help="Used to confirm that this command can be executed.",
        )

    def handle(self, *args, **options):
        if not options.get("confirm", False):
            raise CommandError(self.get_confirmation_message(options))
