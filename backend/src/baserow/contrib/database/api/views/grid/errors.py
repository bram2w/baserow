from rest_framework.status import HTTP_404_NOT_FOUND, HTTP_400_BAD_REQUEST


ERROR_GRID_DOES_NOT_EXIST = (
    "ERROR_GRID_DOES_NOT_EXIST",
    HTTP_404_NOT_FOUND,
    "The requested grid view does not exist.",
)

ERROR_UNRELATED_FIELD = (
    "ERROR_UNRELATED_FIELD",
    HTTP_400_BAD_REQUEST,
    "The field is not related to the provided grid view.",
)
