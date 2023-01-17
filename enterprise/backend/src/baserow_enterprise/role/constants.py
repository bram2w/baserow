from django.conf import settings

DEFAULT_ROLE_ASSIGNABLE_OBJECT_MAP = {
    "group": {
        "READ": "group.read_role",
        "UPDATE": "group.assign_role",
    },
    "application": {
        "READ": "application.read_role",
        "UPDATE": "application.update_role",
    },
    "database_table": {
        "READ": "database.table.read_role",
        "UPDATE": "database.table.update_role",
    },
}

ADMIN_ROLE_UID = "ADMIN"
BUILDER_ROLE_UID = "BUILDER"
EDITOR_ROLE_UID = "EDITOR"
COMMENTER_ROLE_UID = "COMMENTER"
VIEWER_ROLE_UID = "VIEWER"
NO_ACCESS_ROLE_UID = getattr(settings, "NO_ACCESS_ROLE_UID", "NO_ACCESS")
NO_ROLE_LOW_PRIORITY_ROLE_UID = getattr(
    settings, "NO_ROLE_LOW_PRIORITY_UID", "NO_ROLE_LOW_PRIORITY"
)
FREE_ROLE_UIDS = [VIEWER_ROLE_UID, NO_ACCESS_ROLE_UID, NO_ROLE_LOW_PRIORITY_ROLE_UID]

ROLE_ASSIGNABLE_OBJECT_MAP = getattr(
    settings,
    "GET_ROLE_ASSIGNABLE_OBJECT_MAP",
    DEFAULT_ROLE_ASSIGNABLE_OBJECT_MAP,
)
SUBJECT_PRIORITY = getattr(
    settings, "SUBJECT_PRIORITY", ["auth.User", "baserow_enterprise.Team"]
)
