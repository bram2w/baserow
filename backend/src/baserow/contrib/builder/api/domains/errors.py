from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND

ERROR_DOMAIN_DOES_NOT_EXIST = (
    "ERROR_DOMAIN_DOES_NOT_EXIST",
    HTTP_404_NOT_FOUND,
    "The requested domain does not exist.",
)

ERROR_DOMAIN_NOT_IN_BUILDER = (
    "ERROR_DOMAIN_NOT_IN_BUILDER",
    HTTP_400_BAD_REQUEST,
    "The domain id {e.domain_id} does not belong to the builder.",
)

ERROR_ONLY_ONE_DOMAIN_ALLOWED = (
    "ERROR_ONLY_ONE_DOMAIN_ALLOWED",
    HTTP_400_BAD_REQUEST,
    "A builder can only have one domain assigned at the moment. "
    "This might change in the future.",
)
