from django.contrib.auth.models import AbstractUser

from baserow.contrib.database.views.models import View
from baserow.contrib.database.views.operations import UpdateViewOperationType
from baserow.contrib.database.views.registries import ViewOwnershipType
from baserow.core.handler import CoreHandler


class CollaborativeViewOwnershipType(ViewOwnershipType):
    """
    Represents views that are shared between all users that can access
    a specific table.
    """

    type = "collaborative"

    def change_ownership_type(self, user: AbstractUser, view: View) -> View:
        view.ownership_type = self.type
        # The previous permission check (when updating the view) was done using
        # the old ownership_type. Verify that the user has permission to update
        # the view with the new one as well:
        CoreHandler().check_permissions(
            user,
            UpdateViewOperationType.type,
            workspace=view.table.database.workspace,
            context=view,
        )
        view.owned_by = user
        return view
