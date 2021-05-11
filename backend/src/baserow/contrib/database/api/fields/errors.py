from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND


ERROR_FIELD_DOES_NOT_EXIST = (
    "ERROR_FIELD_DOES_NOT_EXIST",
    HTTP_404_NOT_FOUND,
    "The requested field does not exist.",
)
ERROR_CANNOT_DELETE_PRIMARY_FIELD = "ERROR_CANNOT_DELETE_PRIMARY_FIELD"
ERROR_CANNOT_CHANGE_FIELD_TYPE = "ERROR_CANNOT_CHANGE_FIELD_TYPE"
ERROR_LINK_ROW_TABLE_NOT_PROVIDED = (
    "ERROR_LINK_ROW_TABLE_NOT_PROVIDED",
    HTTP_400_BAD_REQUEST,
    "The `link_row_table` must be provided.",
)
ERROR_LINK_ROW_TABLE_NOT_IN_SAME_DATABASE = "ERROR_LINK_ROW_TABLE_NOT_IN_SAME_DATABASE"
ERROR_FIELD_NOT_IN_TABLE = (
    "ERROR_FIELD_NOT_IN_TABLE",
    HTTP_400_BAD_REQUEST,
    "The provided field does not belong in the related table.",
)
ERROR_ORDER_BY_FIELD_NOT_FOUND = (
    "ERROR_ORDER_BY_FIELD_NOT_FOUND",
    HTTP_400_BAD_REQUEST,
    "The field {e.field_name} was not found in the table.",
)
ERROR_ORDER_BY_FIELD_NOT_POSSIBLE = (
    "ERROR_ORDER_BY_FIELD_NOT_POSSIBLE",
    HTTP_400_BAD_REQUEST,
    "It is not possible to order by {e.field_name} because the field type "
    "{e.field_type} does not support filtering.",
)
ERROR_FILTER_FIELD_NOT_FOUND = (
    "ERROR_FILTER_FIELD_NOT_FOUND",
    HTTP_400_BAD_REQUEST,
    "The field {e.field_name} was not found in the table.",
)
ERROR_INCOMPATIBLE_PRIMARY_FIELD_TYPE = (
    "ERROR_INCOMPATIBLE_PRIMARY_FIELD_TYPE",
    HTTP_400_BAD_REQUEST,
    "The field type {e.field_type} is not compatible with the primary field.",
)

ERROR_MAX_FIELD_COUNT_EXCEEDED = "ERROR_MAX_FIELD_COUNT_EXCEEDED"
