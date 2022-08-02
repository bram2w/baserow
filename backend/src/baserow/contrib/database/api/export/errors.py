from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND

ERROR_EXPORT_JOB_DOES_NOT_EXIST = (
    "ERROR_EXPORT_JOB_DOES_NOT_EXIST",
    HTTP_404_NOT_FOUND,
    "That export job does not exist.",
)

ERROR_VIEW_UNSUPPORTED_FOR_EXPORT_TYPE = (
    "ERROR_VIEW_UNSUPPORTED_FOR_EXPORT_TYPE",
    HTTP_400_BAD_REQUEST,
    "You cannot export this view using that exporter type.",
)

ERROR_TABLE_ONLY_EXPORT_UNSUPPORTED = (
    "ERROR_TABLE_ONLY_EXPORT_UNSUPPORTED",
    HTTP_400_BAD_REQUEST,
    "This exporter type does not support exporting just the table.",
)
