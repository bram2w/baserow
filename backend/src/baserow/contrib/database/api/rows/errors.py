from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND

ERROR_ROW_DOES_NOT_EXIST = (
    "ERROR_ROW_DOES_NOT_EXIST",
    HTTP_404_NOT_FOUND,
    "The rows {e.ids} do not exist.",
)

ERROR_ROW_IDS_NOT_UNIQUE = (
    "ERROR_ROW_IDS_NOT_UNIQUE",
    HTTP_400_BAD_REQUEST,
    "The provided row ids {e.ids} are not unique.",
)

ERROR_INVALID_JOIN_PARAMETER = (
    "ERROR_INVALID_JOIN_PARAMETER",
    HTTP_400_BAD_REQUEST,
    "The provided __join query parameter wasn't used correctly.",
)
