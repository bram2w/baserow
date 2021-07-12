from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND


ERROR_FORM_DOES_NOT_EXIST = (
    "ERROR_FORM_DOES_NOT_EXIST",
    HTTP_404_NOT_FOUND,
    "The requested form does not exist.",
)
ERROR_FORM_VIEW_FIELD_TYPE_IS_NOT_SUPPORTED = (
    "ERROR_FORM_VIEW_FIELD_TYPE_IS_NOT_SUPPORTED",
    HTTP_400_BAD_REQUEST,
    "The {e.field_type} field type is not compatible with the form view.",
)
