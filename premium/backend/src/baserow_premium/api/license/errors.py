from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND


ERROR_PREMIUM_LICENSE_DOES_NOT_EXIST = (
    "ERROR_PREMIUM_LICENSE_DOES_NOT_EXIST",
    HTTP_404_NOT_FOUND,
    "The requested license does not exist. Please use the internal `id` and not the "
    "`license_id`.",
)
ERROR_INVALID_PREMIUM_LICENSE = (
    "ERROR_INVALID_PREMIUM_LICENSE",
    HTTP_400_BAD_REQUEST,
    "The provided license is invalid.",
)
ERROR_UNSUPPORTED_PREMIUM_LICENSE = (
    "ERROR_UNSUPPORTED_PREMIUM_LICENSE",
    HTTP_400_BAD_REQUEST,
    "This license version is not supported. You probably need to update your Baserow "
    "installation.",
)
ERROR_PREMIUM_LICENSE_INSTANCE_ID_MISMATCH = (
    "ERROR_PREMIUM_LICENSE_INSTANCE_ID_MISMATCH",
    HTTP_400_BAD_REQUEST,
    "The `instance_id` of the license doesn't match the instance id of Baserow copy.",
)
ERROR_PREMIUM_LICENSE_ALREADY_EXISTS = (
    "ERROR_PREMIUM_LICENSE_ALREADY_EXISTS",
    HTTP_400_BAD_REQUEST,
    "The provided premium license already exists.",
)
ERROR_PREMIUM_LICENSE_HAS_EXPIRED = (
    "ERROR_PREMIUM_LICENSE_HAS_EXPIRED",
    HTTP_400_BAD_REQUEST,
    "The provided premium license has already expired.",
)
ERROR_USER_ALREADY_ON_PREMIUM_LICENSE = (
    "ERROR_USER_ALREADY_IN_PREMIUM_LICENSE",
    HTTP_400_BAD_REQUEST,
    "The provided user is already on the premium license.",
)
ERROR_NO_SEATS_LEFT_IN_PREMIUM_LICENSE = (
    "ERROR_NO_SEATS_LEFT_IN_PREMIUM_LICENSE",
    HTTP_400_BAD_REQUEST,
    "Can't add the user because there are not seats left in the license.",
)
