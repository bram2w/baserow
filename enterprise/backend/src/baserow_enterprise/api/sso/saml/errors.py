from rest_framework.status import HTTP_400_BAD_REQUEST

ERROR_SAML_INVALID_LOGIN_REQUEST = (
    "ERROR_SAML_INVALID_LOGIN_REQUEST",
    HTTP_400_BAD_REQUEST,
    "No identity provider found with the given information.",
)

ERROR_SAML_PROVIDER_FOR_DOMAIN_ALREADY_EXISTS = (
    "ERROR_SAML_PROVIDER_FOR_DOMAIN_ALREADY_EXISTS",
    HTTP_400_BAD_REQUEST,
    "You cannot have two SAML providers with the same domain, please choose a "
    "unique domain for each SAML provider.",
)
