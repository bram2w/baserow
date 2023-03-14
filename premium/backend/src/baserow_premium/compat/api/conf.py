from baserow.compat.api.conf import GROUP_DEPRECATION
from baserow.compat.api.utils import prefix_schema_description_deprecated

# Deprecation warnings prefixed to the group admin endpoint descriptions.
GROUP_ADMIN_DEPRECATION_PREFIXES = {
    "admin_list_groups": prefix_schema_description_deprecated(
        "admin_list_workspaces",
        "#tag/Admin/operation/admin_list_workspaces",
        GROUP_DEPRECATION.year,
    ),
    "admin_delete_group": prefix_schema_description_deprecated(
        "admin_delete_workspace",
        "#tag/Admin/operation/admin_delete_workspace",
        GROUP_DEPRECATION.year,
    ),
}
