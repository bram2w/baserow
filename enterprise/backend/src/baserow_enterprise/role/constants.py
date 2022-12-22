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

NO_ACCESS_ROLE = getattr(settings, "NO_ACCESS_ROLE", "NO_ACCESS")
NO_ROLE_LOW_PRIORITY_ROLE = getattr(
    settings, "NO_ROLE_LOW_PRIORITY_ROLE", "NO_ROLE_LOW_PRIORITY"
)
ROLE_ASSIGNABLE_OBJECT_MAP = getattr(
    settings,
    "GET_ROLE_ASSIGNABLE_OBJECT_MAP",
    DEFAULT_ROLE_ASSIGNABLE_OBJECT_MAP,
)
SUBJECT_PRIORITY = getattr(
    settings, "SUBJECT_PRIORITY", ["auth.User", "baserow_enterprise.Team"]
)
