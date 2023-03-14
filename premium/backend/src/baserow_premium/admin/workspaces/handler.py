from baserow_premium.admin.workspaces.exceptions import CannotDeleteATemplateGroupError
from baserow_premium.license.features import PREMIUM
from baserow_premium.license.handler import LicenseHandler

from baserow.core.exceptions import IsNotAdminError
from baserow.core.signals import workspace_deleted
from baserow.core.trash.handler import TrashHandler


class WorkspacesAdminHandler:
    def delete_workspace(self, user, workspace):
        """
        Deletes an existing workspace and related applications if the user is staff.

        :param user: The user on whose behalf the workspace is deleted
        :type: user: User
        :param workspace: The workspace instance that must be deleted.
        :type: workspace: Workspace
        :raises IsNotAdminError: If the user is not admin or staff.
        """

        LicenseHandler.raise_if_user_doesnt_have_feature_instance_wide(PREMIUM, user)

        if not user.is_staff:
            raise IsNotAdminError()

        if workspace.has_template():
            raise CannotDeleteATemplateGroupError()

        # Load the workspace users before the workspace is deleted so that we can
        # pass those along with the signal.
        workspace_id = workspace.id
        workspace_users = list(workspace.users.all())

        TrashHandler.permanently_delete(workspace)

        workspace_deleted.send(
            self,
            workspace_id=workspace_id,
            workspace=workspace,
            workspace_users=workspace_users,
        )
