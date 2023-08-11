import sys

from django.core.management.base import BaseCommand

from loguru import logger

from baserow.core.notifications.registries import (
    CliNotificationTypeMixin,
    notification_type_registry,
)


class Command(BaseCommand):
    help = "Interactive command to create and send a notification"

    def handle(self, *args, **options):
        available_broadcast_notification_types = [
            notification_type
            for notification_type in notification_type_registry.registry.values()
            if isinstance(notification_type, CliNotificationTypeMixin)
        ]
        numbered_options = "\n".join(
            [
                f"{i + 1} - {notification_type.type}"
                for i, notification_type in enumerate(
                    available_broadcast_notification_types
                )
            ]
        )
        choice = input(f"Available types\n{numbered_options}\n\nChoose a number: ")
        try:
            choice = int(choice)
            if choice < 1 or choice > len(available_broadcast_notification_types):
                raise ValueError()
        except ValueError:
            logger.error(
                f"Invalid choice {choice}. Please choose a number from the "
                "list of options."
            )
            sys.exit(1)

        chosen_type = available_broadcast_notification_types[choice - 1]
        chosen_type.prompt_for_args_in_cli_and_create_notification()
