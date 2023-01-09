from django.contrib.auth import get_user_model
from django.db import transaction

from baserow.core.models import GroupUser
from baserow.core.user.exceptions import UserAlreadyExist
from baserow.core.user.handler import UserHandler

User = get_user_model()


@transaction.atomic
def load_test_data():

    print("Add basic users...")
    user_handler = UserHandler()
    try:
        user = user_handler.create_user("Admin", "admin@baserow.io", "password")
    except UserAlreadyExist:
        user = User.objects.get(email="admin@baserow.io")

    user.is_staff = True
    user.save()

    group = user.groupuser_set.all().order_by("id").first().group
    group.name = "Acme Corp"
    group.save()

    try:
        user = user_handler.create_user("Member", "member@baserow.io", "password")
    except UserAlreadyExist:
        user = User.objects.get(email="member@baserow.io")

    GroupUser.objects.update_or_create(
        group=group, user=user, defaults=dict(permissions="MEMBER", order=1)
    )
