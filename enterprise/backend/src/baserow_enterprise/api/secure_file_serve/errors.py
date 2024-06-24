from rest_framework.status import HTTP_403_FORBIDDEN

ERROR_SECURE_FILE_SERVE_EXCEPTION = (
    "ERROR_SECURE_FILE_SERVE_EXCEPTION",
    HTTP_403_FORBIDDEN,
    "The requested signed data is invalid.",
)
