from django.contrib.auth import get_user_model

from baserow.core.models import GroupUser
from baserow.core.user.exceptions import UserAlreadyExist
from baserow.core.user.handler import UserHandler
from baserow_enterprise.role.default_roles import default_roles

User = get_user_model()


def load_test_data():

    # Get the user created in the main module
    user = User.objects.get(email="admin@baserow.io")
    group = user.groupuser_set.get(group__name="Acme Corp").group

    print("Add one user per existing role in the same group as admin")
    for i, r in enumerate(default_roles.keys()):
        rl = r.lower()
        try:
            user = UserHandler().create_user(rl, f"{rl}@baserow.io", "password")
        except UserAlreadyExist:
            user = User.objects.get(email=f"{rl}@baserow.io")

        GroupUser.objects.update_or_create(
            group=group, user=user, defaults=dict(permissions=r, order=i + 1)
        )
