from rest_framework.status import HTTP_400_BAD_REQUEST

ERROR_CANNOT_UPDATE_PREMIUM_ATTRIBUTES_ON_TEMPLATE = (
    "ERROR_CANNOT_UPDATE_PREMIUM_ATTRIBUTES_ON_TEMPLATE",
    HTTP_400_BAD_REQUEST,
    "The provided group is a template and cannot be updated.",
)

ERROR_INVALID_SELECT_OPTION_PARAMETER = (
    "ERROR_INVALID_SELECT_OPTION_PARAMETER",
    HTTP_400_BAD_REQUEST,
    "The provided select option parameter {e.select_option_name} is invalid. The "
    "following structure is expected ?select_option=id,limit,offset (e.g. "
    "?select_option=1,2,3).",
)
