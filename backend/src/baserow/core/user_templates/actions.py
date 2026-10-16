import dataclasses
from typing import Callable, Iterable, List, Optional

from django.contrib.auth.models import AbstractUser
from django.db import transaction
from django.utils.translation import gettext_lazy as _

from baserow.core.action.registries import (
    ActionScopeStr,
    ActionType,
    ActionTypeDescription,
)
from baserow.core.action.scopes import (
    WORKSPACE_ACTION_CONTEXT,
    WorkspaceActionScopeType,
)
from baserow.core.models import Template, Workspace
from baserow.core.user_templates.handler import UserTemplateHandler
from baserow.core.user_templates.service import UserTemplateService
from baserow.core.utils import ChildProgressBuilder


class CreateUserTemplateActionType(ActionType):
    type = "create_user_template"
    description = ActionTypeDescription(
        _("Create template"),
        _(
            'Template "%(template_name)s" (%(template_id)s) created from '
            "applications %(application_ids)s"
        ),
        WORKSPACE_ACTION_CONTEXT,
    )
    analytics_params = [
        "template_id",
        "workspace_id",
        "application_ids",
    ]

    @dataclasses.dataclass
    class Params:
        template_id: int
        template_name: str
        workspace_id: int
        workspace_name: str
        application_ids: List[int]

    @classmethod
    def do(
        cls,
        user: AbstractUser,
        workspace: Workspace,
        application_ids: List[int],
        *,
        name: str,
        description: str,
        icon: str,
        category_ids: Iterable[int],
        progress_builder: Optional[ChildProgressBuilder] = None,
        track_content: Optional[Callable[..., None]] = None,
        before_commit: Optional[Callable[[Template], None]] = None,
    ) -> Template:
        """
        Creates a private user template from applications of the workspace. This
        action is not undoable.

        The applications are copied first, in transactions of their own, see
        `UserTemplateHandler.copy_applications`. The template and the action are
        then created in one transaction, which a cancellation of the job noticed
        before it commits rolls back.

        :param user: The user creating the template.
        :param workspace: The workspace the applications are copied from.
        :param application_ids: The ids of the selected applications.
        :param name: The name of the template.
        :param description: The description of the template.
        :param icon: The icon class name, one of `USER_TEMPLATE_ICONS`.
        :param category_ids: The ids of the existing categories of the template.
        :param progress_builder: A progress builder that allows for publishing
            progress.
        :param track_content: Called with the content created so far.
        :param before_commit: Called with the template as the last step of its
            transaction, and can still roll it back by raising.
        :return: The created template.
        """

        progress = ChildProgressBuilder.build(progress_builder, child_total=100)
        template_workspace, archive_name = UserTemplateService().copy_applications(
            user,
            workspace,
            application_ids,
            name=name,
            progress_builder=progress.create_child_builder(represents_progress=99),
            track_content=track_content,
        )

        with transaction.atomic():
            template = UserTemplateHandler().create_template_root(
                owner=user,
                name=name,
                description=description,
                icon=icon,
                category_ids=category_ids,
                workspace=template_workspace,
                archive=archive_name,
                metadata=UserTemplateHandler().build_template_metadata(
                    workspace, application_ids
                ),
            )
            params = cls.Params(
                template_id=template.id,
                template_name=template.name,
                workspace_id=workspace.id,
                workspace_name=workspace.name,
                application_ids=list(application_ids),
            )
            cls.register_action(
                user, params, cls.scope(workspace.id), workspace=workspace
            )
            progress.increment()
            if before_commit is not None:
                before_commit(template)

        return template

    @classmethod
    def scope(cls, workspace_id: int) -> ActionScopeStr:
        return WorkspaceActionScopeType.value(workspace_id)
