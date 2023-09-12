from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND

ERROR_DATA_SOURCE_DOES_NOT_EXIST = (
    "ERROR_DATA_SOURCE_DOES_NOT_EXIST",
    HTTP_404_NOT_FOUND,
    "The requested data_source does not exist.",
)

ERROR_DATA_SOURCE_IMPROPERLY_CONFIGURED = (
    "ERROR_DATA_SOURCE_IMPROPERLY_CONFIGURED",
    HTTP_400_BAD_REQUEST,
    "The data_source configuration is incorrect: {e}",
)


ERROR_DATA_SOURCE_NOT_IN_SAME_PAGE = (
    "ERROR_DATA_SOURCE_NOT_IN_SAME_PAGE",
    HTTP_400_BAD_REQUEST,
    "The given data_sources do not belong to the same page.",
)

ERROR_DATA_DOES_NOT_EXIST = (
    "ERROR_DATA_SOURCE_DOES_NOT_EXIST",
    HTTP_404_NOT_FOUND,
    "The requested data does not exist.",
)
