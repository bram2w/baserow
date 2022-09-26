from rest_framework.status import HTTP_400_BAD_REQUEST

ERROR_CANNOT_UPDATE_PREMIUM_ATTRIBUTES_ON_TEMPLATE = (
    "ERROR_CANNOT_UPDATE_PREMIUM_ATTRIBUTES_ON_TEMPLATE",
    HTTP_400_BAD_REQUEST,
    "The provided group is a template and cannot be updated.",
)
