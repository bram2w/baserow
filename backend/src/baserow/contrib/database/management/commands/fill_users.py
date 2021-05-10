import uuid

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from faker import Faker

from baserow.core.models import Group, GroupUser, GROUP_USER_PERMISSION_ADMIN

User = get_user_model()


class Command(BaseCommand):
    help = "Fills baserow with random users."

    def add_arguments(self, parser):
        parser.add_argument(
            "limit", type=int, help="Amount of users that need to be inserted."
        )

    def handle(self, *args, **options):
        limit = options["limit"]
        fake = Faker()

        email_prefix = (
            "baserow_prefix_to_ensure_we_never_accidentally_email_a_real_person_"
        )

        clashing_email_counter = 0
        for i in range(limit):
            username = email_prefix + fake.email()
            password = str(uuid.uuid4())
            name = fake.name()

            # The fake email generator often creates the same email over and over,
            # user a simple counter to ensure username uniqueness so we can insert
            # the user successfully.
            if User.objects.filter(username=username).exists():
                username = str(clashing_email_counter) + username
                clashing_email_counter += 1

            user = User(first_name=name, email=username, username=username)
            user.set_password(password)
            user.save()

            group = Group.objects.create(name=name + "'s Group")
            GroupUser.objects.create(
                group=group,
                user=user,
                order=0,
                permissions=GROUP_USER_PERMISSION_ADMIN,
            )

        self.stdout.write(self.style.SUCCESS(f"{limit} rows have been inserted."))
