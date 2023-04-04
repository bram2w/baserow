from baserow.compat.api.conf import GROUP_DEPRECATION
from baserow.compat.api.utils import prefix_schema_description_deprecated

# Deprecation warnings prefixed to the group teams descriptions.
TEAMS_DEPRECATION_PREFIXES = {
    "group_list_teams": prefix_schema_description_deprecated(
        "workspace_list_teams",
        "#tag/Teams/operation/workspace_list_teams",
        GROUP_DEPRECATION.year,
    ),
    "group_create_team": prefix_schema_description_deprecated(
        "workspace_create_team",
        "#tag/Teams/operation/create_workspace",
        GROUP_DEPRECATION.year,
    ),
}

# Deprecation warnings prefixed to the group teams descriptions.
ROLE_DEPRECATION_PREFIXES = {
    "group_assign_role": prefix_schema_description_deprecated(
        "workspace_assign_role",
        "#tag/Role-assignments/operation/workspace_assign_role",
        GROUP_DEPRECATION.year,
    ),
    "group_list_role_assignments": prefix_schema_description_deprecated(
        "workspace_list_role_assignments",
        "#tag/Role-assignments/operation/workspace_list_role_assignments",
        GROUP_DEPRECATION.year,
    ),
    "group_batch_assign_role": prefix_schema_description_deprecated(
        "workspace_batch_assign_role",
        "#tag/Role-assignments/operation/workspace_batch_assign_role",
        GROUP_DEPRECATION.year,
    ),
}
