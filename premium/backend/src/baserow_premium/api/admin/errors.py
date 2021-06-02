from rest_framework.status import HTTP_400_BAD_REQUEST


ERROR_ADMIN_LISTING_INVALID_SORT_DIRECTION = (
    "ERROR_ADMIN_LISTING_INVALID_SORT_DIRECTION",
    HTTP_400_BAD_REQUEST,
    "Attributes to sort by must be prefixed with one of '-' or '+'.",
)
ERROR_ADMIN_LISTING_INVALID_SORT_ATTRIBUTE = (
    "ERROR_ADMIN_LISTING_INVALID_SORT_ATTRIBUTE",
    HTTP_400_BAD_REQUEST,
    "Invalid attribute name provided to sort by.",
)
