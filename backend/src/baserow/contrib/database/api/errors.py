from rest_framework.status import HTTP_400_BAD_REQUEST


ERROR_DATABASE_DOES_NOT_BELONG_TO_GROUP = (
    "ERROR_DATABASE_DOES_NOT_BELONG_TO_GROUP",
    HTTP_400_BAD_REQUEST,
    "The provided database does not belong to the related group.",
)
