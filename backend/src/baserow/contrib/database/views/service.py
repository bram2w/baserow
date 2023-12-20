from django.contrib.auth.models import AbstractUser

from baserow.contrib.database.views.handler import ViewHandler
from baserow.contrib.database.views.models import View
from baserow.contrib.database.views.operations import ReadViewOperationType
from baserow.core.handler import CoreHandler


class ViewService:
    def __init__(self):
        self.handler = ViewHandler()

    def get_view(self, user: AbstractUser, view_id: int) -> View:
        """
        Returns a view instance from the database. Also checks the user
        permissions.

        :param user: The user trying to get the view.
        :param view_id: The ID of the view.
        :return: The view instance.
        """

        view = self.handler.get_view(view_id)

        CoreHandler().check_permissions(
            user,
            ReadViewOperationType.type,
            workspace=view.table.database.workspace,
            context=view,
        )

        return view
