from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND

ERROR_GRID_DOES_NOT_EXIST = (
    "ERROR_GRID_DOES_NOT_EXIST",
    HTTP_404_NOT_FOUND,
    "The requested grid view does not exist.",
)

ERROR_AGGREGATION_DOES_NOT_SUPPORTED_FIELD = (
    "ERROR_AGGREGATION_DOES_NOT_SUPPORTED_FIELD",
    HTTP_400_BAD_REQUEST,
    "The aggregation type does not support the given field.",
)
