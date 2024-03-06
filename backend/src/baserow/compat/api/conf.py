from datetime import datetime, timezone

from baserow.compat.api.utils import prefix_schema_description_deprecated

# When will `Group` be removed in favor of `Workspace`?
deprecation_tz = timezone.utc
GROUP_DEPRECATION = datetime(2024, 4, 1, tzinfo=deprecation_tz)

# Deprecation warnings prefixed to the group endpoint descriptions.
GROUP_DEPRECATION_PREFIXES = {
    "list_groups": prefix_schema_description_deprecated(
        "list_workspaces",
        "#tag/Workspaces/operation/list_workspaces",
        GROUP_DEPRECATION.year,
    ),
    "create_group": prefix_schema_description_deprecated(
        "create_workspace",
        "#tag/Workspaces/operation/create_workspace",
        GROUP_DEPRECATION.year,
    ),
    "update_group": prefix_schema_description_deprecated(
        "update_workspace",
        "#tag/Workspaces/operation/update_workspace",
        GROUP_DEPRECATION.year,
    ),
    "delete_group": prefix_schema_description_deprecated(
        "delete_workspace",
        "#tag/Workspaces/operation/delete_workspace",
        GROUP_DEPRECATION.year,
    ),
    "leave_group": prefix_schema_description_deprecated(
        "leave_workspace",
        "#tag/Workspaces/operation/leave_workspace",
        GROUP_DEPRECATION.year,
    ),
    "order_groups": prefix_schema_description_deprecated(
        "order_workspaces",
        "#tag/Workspaces/operation/order_workspaces",
        GROUP_DEPRECATION.year,
    ),
    "group_permissions": prefix_schema_description_deprecated(
        "workspace_permissions",
        "#tag/Workspaces/operation/workspace_permissions",
        GROUP_DEPRECATION.year,
    ),
}

# Deprecation warnings prefixed to the group user endpoint descriptions.
GROUP_USER_DEPRECATION_PREFIXES = {
    "list_group_users": prefix_schema_description_deprecated(
        "list_workspace_users", "#tag/Workspaces/operation/list_workspace_users"
    ),
    "update_group_user": prefix_schema_description_deprecated(
        "update_workspace_user", "#tag/Workspaces/operation/update_workspace_user"
    ),
    "delete_group_user": prefix_schema_description_deprecated(
        "delete_workspace_user", "#tag/Workspaces/operation/delete_workspace_user"
    ),
}

# Deprecation warnings prefixed to the group invitation endpoint descriptions.
INVITATION_DEPRECATION_PREFIXES = {
    "list_group_invitations": prefix_schema_description_deprecated(
        "list_workspace_invitations",
        "#tag/Workspace-invitations/operation/list_workspace_invitations",
        GROUP_DEPRECATION.year,
    ),
    "create_group_invitation": prefix_schema_description_deprecated(
        "create_workspace_invitation",
        "#tag/Workspace-invitations/operation/create_workspace_invitation",
        GROUP_DEPRECATION.year,
    ),
    "get_group_invitation": prefix_schema_description_deprecated(
        "get_workspace_invitation",
        "#tag/Workspace-invitations/operation/get_workspace_invitation",
        GROUP_DEPRECATION.year,
    ),
    "update_group_invitation": prefix_schema_description_deprecated(
        "update_workspace_invitation",
        "#tag/Workspace-invitations/operation/update_workspace_invitation",
        GROUP_DEPRECATION.year,
    ),
    "delete_group_invitation": prefix_schema_description_deprecated(
        "delete_workspace_invitation",
        "#tag/Workspace-invitations/operation/delete_workspace_invitation",
        GROUP_DEPRECATION.year,
    ),
    "accept_group_invitation": prefix_schema_description_deprecated(
        "accept_workspace_invitation",
        "#tag/Workspace-invitations/operation/accept_workspace_invitation",
        GROUP_DEPRECATION.year,
    ),
    "reject_group_invitation": prefix_schema_description_deprecated(
        "reject_workspace_invitation",
        "#tag/Workspace-invitations/operation/reject_workspace_invitation",
        GROUP_DEPRECATION.year,
    ),
    "get_group_invitation_by_token": prefix_schema_description_deprecated(
        "get_workspace_invitation_by_token",
        "#tag/Workspace-invitations/operation/get_workspace_invitation_by_token",
        GROUP_DEPRECATION.year,
    ),
}

# Deprecation warnings prefixed to the group trash endpoint descriptions.
TRASH_DEPRECATION_PREFIXES = {
    "group_get_contents": prefix_schema_description_deprecated(
        "workspace_get_contents",
        "#tag/Trash/operation/workspace_get_contents",
        GROUP_DEPRECATION.year,
    ),
    "group_empty_contents": prefix_schema_description_deprecated(
        "workspace_empty_contents",
        "#tag/Trash/operation/workspace_empty_contents",
        GROUP_DEPRECATION.year,
    ),
}

# Deprecation warnings prefixed to the group application endpoint descriptions.
APPLICATION_DEPRECATION_PREFIXES = {
    "group_list_applications": prefix_schema_description_deprecated(
        "workspace_list_applications",
        "#tag/Applications/operation/workspace_list_applications",
        GROUP_DEPRECATION.year,
    ),
    "group_create_application": prefix_schema_description_deprecated(
        "workspace_create_application",
        "#tag/Applications/operation/workspace_create_application",
        GROUP_DEPRECATION.year,
    ),
    "group_order_applications": prefix_schema_description_deprecated(
        "workspace_order_applications",
        "#tag/Applications/operation/workspace_order_applications",
        GROUP_DEPRECATION.year,
    ),
}


# Deprecation warnings prefixed to the group application endpoint descriptions.
TEMPLATES_DEPRECATION_PREFIXES = {
    "group_list_templates": prefix_schema_description_deprecated(
        "workspace_list_templates",
        "#tag/Templates/operation/workspace_list_templates",
        GROUP_DEPRECATION.year,
    ),
    "group_install_template": prefix_schema_description_deprecated(
        "workspace_install_template",
        "#tag/Templates/operation/workspace_install_template",
        GROUP_DEPRECATION.year,
    ),
    "group_install_template_async": prefix_schema_description_deprecated(
        "workspace_install_template_async",
        "#tag/Templates/operation/workspace_install_template_async",
        GROUP_DEPRECATION.year,
    ),
}
