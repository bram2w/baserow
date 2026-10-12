from django.contrib.contenttypes.models import ContentType

from baserow.core.exceptions import PermissionDenied
from baserow.core.models import Application, WorkspaceUser
from baserow.core.permission_manager import (
    AllowIfTemplatePermissionManagerType as CoreAllowIfTemplatePermissionManagerType,
)
from baserow.core.registries import PermissionManagerType
from baserow.core.subjects import UserSubjectType
from baserow_enterprise.role.constants import (
    ADMIN_ROLE_UID,
    BUILDER_ROLE_UID,
    EDITOR_ROLE_UID,
)

from .models import AgentApplication, AgentChatMinRole
from .operations import (
    ContinueTriggeredAgentChatOperationType,
    ListAgentChatsOperationType,
    ListAgentToolsOperationType,
    ReadAgentChatChannelOperationType,
    ReadAgentChatOperationType,
    ReadAgentDefinitionOperationType,
    ReadAgentTriggerOperationType,
    ReadAgentUsageOperationType,
    StartAgentChatOperationType,
)

# The application field holding the minimum role, per operation.
MIN_ROLE_FIELD_BY_OPERATION = {
    StartAgentChatOperationType.type: "start_chat_min_role",
    ContinueTriggeredAgentChatOperationType.type: "continue_chat_min_role",
}
ROLE_UIDS_BY_MIN_ROLE = {
    AgentChatMinRole.EDITOR: {EDITOR_ROLE_UID, BUILDER_ROLE_UID, ADMIN_ROLE_UID},
    AgentChatMinRole.BUILDER: {BUILDER_ROLE_UID, ADMIN_ROLE_UID},
    AgentChatMinRole.ADMIN: {ADMIN_ROLE_UID},
    AgentChatMinRole.NOBODY: set(),
}


def get_role_uids(actor, workspace, applications) -> tuple[set, dict]:
    """
    The role uids the actor has in the workspace and on each application.
    Without role based access a workspace admin counts as an admin and a
    member as a builder, because members may build everything there.

    :return: The workspace level uids and the uids per application id.
    """

    from baserow_enterprise.role.handler import RoleAssignmentHandler
    from baserow_enterprise.role.permission_manager import RolePermissionManagerType

    if RolePermissionManagerType().is_enabled(workspace):
        handler = RoleAssignmentHandler()
        roles_per_scope = handler.get_roles_per_scope(workspace, actor)
        cache = {}

        def uids(context):
            return {
                role.uid
                for role in handler.get_computed_roles(roles_per_scope, context, cache)
            }

        return uids(workspace), {
            application.id: uids(application) for application in applications
        }

    permissions = (
        WorkspaceUser.objects.filter(workspace=workspace, user=actor)
        .values_list("permissions", flat=True)
        .first()
    )
    if permissions is None:
        role_uids = set()
    elif permissions == "ADMIN":
        role_uids = {ADMIN_ROLE_UID}
    else:
        role_uids = {BUILDER_ROLE_UID}
    return role_uids, {application.id: role_uids for application in applications}


class AgentChatRolePermissionManagerType(PermissionManagerType):
    """
    Applies the minimum roles an agent application sets for starting a
    conversation and for continuing one that a trigger started. It only
    denies: allowed checks fall through, so the role and basic managers
    still decide whether the actor may run conversations at all.
    """

    type = "agent_chat_role"
    supported_actor_types = [UserSubjectType.type]

    def check_multiple_permissions(self, checks, workspace=None, include_trash=False):
        pertinent = [
            check
            for check in checks
            if check.operation_name in MIN_ROLE_FIELD_BY_OPERATION
            and isinstance(check.context, Application)
        ]
        if workspace is None or not pertinent:
            return {}

        min_roles = {
            values["id"]: values
            for values in AgentApplication.objects.filter(
                id__in={check.context.id for check in pertinent}
            ).values("id", *MIN_ROLE_FIELD_BY_OPERATION.values())
        }
        role_uids_by_actor = {}
        result = {}
        for check in pertinent:
            min_role = min_roles.get(check.context.id, {}).get(
                MIN_ROLE_FIELD_BY_OPERATION[check.operation_name],
                AgentChatMinRole.EDITOR,
            )
            if min_role == AgentChatMinRole.EDITOR:
                continue
            if check.actor not in role_uids_by_actor:
                role_uids_by_actor[check.actor] = get_role_uids(
                    check.actor, workspace, [c.context for c in pertinent]
                )[1]
            role_uids = role_uids_by_actor[check.actor].get(check.context.id, set())
            if not role_uids & ROLE_UIDS_BY_MIN_ROLE[min_role]:
                result[check] = PermissionDenied()
        return result

    def get_permissions_object(self, actor, workspace=None):
        """
        The actor's role uids so the frontend can compare them with the
        application's minimum roles, which change live with the application.
        Applications created later fall back to the workspace level roles.
        """

        if workspace is None:
            return None

        applications = list(
            Application.objects.filter(
                workspace=workspace,
                content_type=ContentType.objects.get_for_model(AgentApplication),
            ).only("id", "workspace_id")
        )
        if not applications:
            # Nothing to restrict; keeps the role lookup off other workspaces.
            return None
        default, by_application = get_role_uids(actor, workspace, applications)
        return {
            "default": sorted(default),
            "applications": {
                application_id: sorted(uids)
                for application_id, uids in by_application.items()
            },
        }


class AllowIfTemplatePermissionManagerType(CoreAllowIfTemplatePermissionManagerType):
    """
    Allows the read operations of the agent application on template
    workspaces, so an agent can be previewed as part of a template.
    """

    AGENT_OPERATION_ALLOWED_ON_TEMPLATES = [
        ReadAgentDefinitionOperationType.type,
        ReadAgentTriggerOperationType.type,
        ListAgentToolsOperationType.type,
        ListAgentChatsOperationType.type,
        ReadAgentChatOperationType.type,
        ReadAgentChatChannelOperationType.type,
        ReadAgentUsageOperationType.type,
    ]

    @property
    def OPERATION_ALLOWED_ON_TEMPLATES(self):
        return (
            self.prev_manager_type.OPERATION_ALLOWED_ON_TEMPLATES
            + self.AGENT_OPERATION_ALLOWED_ON_TEMPLATES
        )

    def __init__(self, prev_manager_type: PermissionManagerType):
        self.prev_manager_type = prev_manager_type
