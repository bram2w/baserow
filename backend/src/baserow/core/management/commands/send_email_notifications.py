import sys
from datetime import datetime, timezone

from django.core.management.base import BaseCommand
from django.db.models import Q

from loguru import logger

from baserow.core.models import User, UserProfile
from baserow.core.notifications.handler import NotificationHandler
from baserow.core.notifications.tasks import (
    send_daily_notifications_email_to_users,
    send_instant_notifications_email_to_users,
    send_weekly_notifications_email_to_users,
)


def send_notifications_to_users_with_frequency(frequency, timestamp):
    if timestamp is not None:
        timestamp = datetime.fromisoformat(timestamp)
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)

    if frequency == UserProfile.EmailNotificationFrequencyOptions.INSTANT.value:
        return send_instant_notifications_email_to_users()
    elif frequency == UserProfile.EmailNotificationFrequencyOptions.DAILY.value:
        return send_daily_notifications_email_to_users(timestamp)
    elif frequency == UserProfile.EmailNotificationFrequencyOptions.WEEKLY.value:
        return send_weekly_notifications_email_to_users(timestamp)


class Command(BaseCommand):
    help = "Sends email notifications to users with the provided user setting or the provided user id."

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument(
            "-f",
            "--frequency",
            type=str,
            choices=[x.value for x in UserProfile.EmailNotificationFrequencyOptions],
            help=(
                "Filter users to notify by email based on the email_notification_frequency "
                "profile settings (instant, daily, weekly)."
            ),
        )
        parser.add_argument(
            "-t",
            "--timestamp",
            type=str,
            help=(
                "This is an ISO timestamp used to schedule the command for execution at a specified time. "
                "This argument is particularly useful for sending daily and weekly notifications to users "
                "in specific timezones. For instance, if EMAIL_NOTIFICATIONS_DAILY_HOUR_OF_DAY is set "
                "to 14 (2 PM), you can provide the timestamp of 2023-08-01T12:00:00 to send daily email "
                "notifications to all users in the UTC+2 timezone (i.e. Europe/Rome)."
            ),
        )
        parser.add_argument(
            "-l",
            "--limit",
            type=int,
            default=None,
            help="The maximum number of emails to send.",
        )
        parser.add_argument(
            "-uid",
            "--user-id",
            type=int,
            default=None,
            help="The id of the user to send the email notifications to.",
        )

    def handle(self, *args, **options):
        frequency = options["frequency"]
        max_emails = options["limit"]
        user_id = options["user_id"]
        timestamp = options["timestamp"]

        if user_id is not None and not frequency:
            result = NotificationHandler.send_unread_notifications_by_email_to_users_matching_filters(
                Q(id=user_id), max_emails=max_emails
            )
            logger.info(
                f"Sent {len(result.users_with_notifications)} email "
                f"notifications to {User.objects.get(pk=user_id).email} (id={user_id})"
            )
        elif frequency is not None:
            result = send_notifications_to_users_with_frequency(frequency, timestamp)
            logger.info(
                f"Sent {len(result.users_with_notifications)} email "
                f"notifications to users with the frequency set to {frequency}."
            )
        else:
            print("Please provide one between --frequency or --user-id.\n")
            self.print_help(sys.argv[0], sys.argv[1])
