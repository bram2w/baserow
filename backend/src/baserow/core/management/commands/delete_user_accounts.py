from datetime import timedelta

from django.core.management.base import BaseCommand

from baserow.core.user.handler import UserHandler


class Command(BaseCommand):
    help = "Deletes all user accounts scheduled for deletion without grace period"

    def handle(self, *args, **options):
        UserHandler().delete_expired_users_and_related_workspaces_if_last_admin(
            grace_delay=timedelta(seconds=0)
        )
