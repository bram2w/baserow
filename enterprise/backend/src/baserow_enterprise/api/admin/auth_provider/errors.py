from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND

ERROR_AUTH_PROVIDER_DOES_NOT_EXIST = (
    "ERROR_AUTH_PROVIDER_DOES_NOT_EXIST",
    HTTP_404_NOT_FOUND,
    "The requested auth provider does not exist.",
)

ERROR_AUTH_PROVIDER_CANNOT_BE_CREATED = (
    "ERROR_AUTH_PROVIDER_CANNOT_BE_CREATED",
    HTTP_400_BAD_REQUEST,
    "The provider type cannot be created.",
)

ERROR_AUTH_PROVIDER_CANNOT_BE_DELETED = (
    "ERROR_AUTH_PROVIDER_CANNOT_BE_DELETED",
    HTTP_400_BAD_REQUEST,
    "The provider type cannot be deleted.",
)

ERROR_CANNOT_DISABLE_ALL_AUTH_PROVIDERS = (
    "ERROR_CANNOT_DISABLE_ALL_AUTH_PROVIDERS",
    HTTP_400_BAD_REQUEST,
    "The last enabled provider cannot be disabled.",
)
