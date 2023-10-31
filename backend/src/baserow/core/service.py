from typing import Optional

from django.contrib.auth.models import AbstractUser
from django.db.models import QuerySet

from baserow.core.handler import CoreHandler
from baserow.core.models import Application
from baserow.core.operations import ListApplicationsWorkspaceOperationType


class CoreService:
    def __init__(self):
        self.handler = CoreHandler()

    def list_applications_in_workspace(
        self,
        user: AbstractUser,
        workspace_id: int,
        base_queryset: Optional[QuerySet] = None,
    ) -> QuerySet:
        """
        Get a list of all the applications in a workspace.

        :param user: The user trying to access the applications
        :param workspace_id: The id of the workspace that has the applications
        :param base_queryset: The base queryset from where to select the applications
        :return: A list of applications
        """

        if base_queryset is None:
            base_queryset = Application.objects

        workspace = self.handler.get_workspace(workspace_id)
        base_queryset = base_queryset.filter(
            workspace=workspace, workspace__trashed=False
        )

        base_queryset = CoreHandler().filter_queryset(
            user,
            ListApplicationsWorkspaceOperationType.type,
            base_queryset,
            workspace=workspace,
        )

        return self.handler.list_applications_in_workspace(workspace_id, base_queryset)
