from django.contrib.auth import get_user_model

from baserow.core.models import WorkspaceUser
from baserow.core.user.exceptions import UserAlreadyExist
from baserow.core.user.handler import UserHandler
from baserow_enterprise.role.default_roles import default_roles

User = get_user_model()


def load_test_data():

    # Get the user created in the main module
    user = User.objects.get(email="admin@baserow.io")
    workspace = user.workspaceuser_set.get(workspace__name="Acme Corp").workspace

    print("Add one user per existing role in the same workspace as admin")
    for i, r in enumerate(default_roles.keys()):
        rl = r.lower()
        try:
            user = UserHandler().create_user(rl, f"{rl}@baserow.io", "password")
        except UserAlreadyExist:
            user = User.objects.get(email=f"{rl}@baserow.io")

        WorkspaceUser.objects.update_or_create(
            workspace=workspace, user=user, defaults=dict(permissions=r, order=i + 1)
        )
