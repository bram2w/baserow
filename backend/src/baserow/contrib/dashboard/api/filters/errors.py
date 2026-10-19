from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND

ERROR_DASHBOARD_FILTER_DOES_NOT_EXIST = (
    "ERROR_DASHBOARD_FILTER_DOES_NOT_EXIST",
    HTTP_404_NOT_FOUND,
    "The requested dashboard filter does not exist.",
)

ERROR_DASHBOARD_FILTER_INVALID_BINDING = (
    "ERROR_DASHBOARD_FILTER_INVALID_BINDING",
    HTTP_400_BAD_REQUEST,
    "Each dashboard table must be mapped to a compatible field.",
)
