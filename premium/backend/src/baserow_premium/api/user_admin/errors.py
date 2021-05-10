from rest_framework.status import HTTP_400_BAD_REQUEST


USER_ADMIN_INVALID_SORT_DIRECTION = (
    "USER_ADMIN_INVALID_SORT_DIRECTION",
    HTTP_400_BAD_REQUEST,
    "Attributes to sort by must be prefixed with one of '-' or '+'.",
)

USER_ADMIN_INVALID_SORT_ATTRIBUTE = (
    "USER_ADMIN_INVALID_SORT_ATTRIBUTE",
    HTTP_400_BAD_REQUEST,
    "Invalid attribute name provided to sort by.",
)

USER_ADMIN_CANNOT_DEACTIVATE_SELF = (
    "USER_ADMIN_CANNOT_DEACTIVATE_SELF",
    HTTP_400_BAD_REQUEST,
    "You cannot de-activate or un-staff yourself.",
)

USER_ADMIN_CANNOT_DELETE_SELF = (
    "USER_ADMIN_CANNOT_DELETE_SELF",
    HTTP_400_BAD_REQUEST,
    "You cannot delete yourself.",
)

USER_ADMIN_UNKNOWN_USER = (
    "USER_ADMIN_UNKNOWN_USER",
    HTTP_400_BAD_REQUEST,
    "Unknown user supplied.",
)
