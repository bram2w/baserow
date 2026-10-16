from typing import Callable, List, Optional, Tuple

from django.contrib.auth.models import AbstractUser
from django.db.models import QuerySet

from baserow.core.exceptions import PermissionDenied
from baserow.core.feature_flags import FF_USER_TEMPLATES, feature_flag_is_enabled
from baserow.core.handler import CoreHandler
from baserow.core.models import Application, Template, Workspace
from baserow.core.operations import (
    ExportWorkspaceOperationType,
    ListApplicationsWorkspaceOperationType,
)
from baserow.core.user_templates.exceptions import NoApplicationsSelected
from baserow.core.user_templates.handler import UserTemplateHandler
from baserow.core.utils import ChildProgressBuilder


class UserTemplateService:
    def list_own_templates(self, user: AbstractUser) -> QuerySet[Template]:
        """
        Returns the user templates owned by the user, newest first.

        :param user: The user whose templates are listed.
        :raises FeatureDisabledException: If user templates are disabled.
        :return: The templates of the user.
        """

        feature_flag_is_enabled(FF_USER_TEMPLATES, raise_if_disabled=True)

        return UserTemplateHandler().list_own_templates(user)

    def get_exportable_applications(
        self, user: AbstractUser, workspace: Workspace, application_ids: List[int]
    ) -> List[Application]:
        """
        Returns the applications the user can copy into a template. Copying needs
        the same permission as exporting the workspace.

        :param user: The user creating the template.
        :param workspace: The workspace the applications are copied from.
        :param application_ids: The ids of the selected applications.
        :raises FeatureDisabledException: If user templates are disabled.
        :raises NoApplicationsSelected: If no application is selected.
        :raises PermissionDenied: If the user can't export the workspace, the
            workspace holds a template, or one of the applications doesn't exist
            or isn't visible to the user.
        :return: The selected applications.
        """

        feature_flag_is_enabled(FF_USER_TEMPLATES, raise_if_disabled=True)

        if not application_ids:
            raise NoApplicationsSelected("At least one application must be selected.")

        CoreHandler().check_permissions(
            user,
            ExportWorkspaceOperationType.type,
            workspace=workspace,
            context=workspace,
        )

        if workspace.has_template():
            raise PermissionDenied("A template can't be created from a template.")

        application_ids = set(application_ids)
        applications = CoreHandler().filter_queryset(
            user,
            ListApplicationsWorkspaceOperationType.type,
            Application.objects.filter(
                workspace=workspace, workspace__trashed=False, id__in=application_ids
            ),
            workspace=workspace,
        )
        applications = list(applications)

        if len(applications) != len(application_ids):
            raise PermissionDenied(
                "Some of the selected applications do not exist or the user does "
                "not have access to them."
            )

        return applications

    def copy_applications(
        self,
        user: AbstractUser,
        workspace: Workspace,
        application_ids: List[int],
        *,
        name: str,
        progress_builder: Optional[ChildProgressBuilder] = None,
        track_content: Optional[Callable[..., None]] = None,
    ) -> Tuple[Workspace, str]:
        """
        Copies applications of the workspace into the content of a new user
        template. See `UserTemplateHandler.copy_applications` for further details.

        :param user: The user creating the template.
        :param workspace: The workspace the applications are copied from.
        :param application_ids: The ids of the selected applications.
        :param name: The name of the template.
        :param progress_builder: A progress builder that allows for publishing
            progress.
        :param track_content: Called with the content created so far.
        :raises FeatureDisabledException: If user templates are disabled.
        :raises NoApplicationsSelected: If no application is selected.
        :raises PermissionDenied: If the user can't copy the applications.
        :return: The workspace holding the copy and the name of the stored archive.
        """

        applications = self.get_exportable_applications(
            user, workspace, application_ids
        )
        return UserTemplateHandler().copy_applications(
            user,
            applications,
            name=name,
            progress_builder=progress_builder,
            track_content=track_content,
        )
