from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND

ERROR_JOB_DOES_NOT_EXIST = (
    "ERROR_JOB_DOES_NOT_EXIST",
    HTTP_404_NOT_FOUND,
    "The requested job does not exist.",
)
ERROR_MAX_JOB_COUNT_EXCEEDED = (
    "ERROR_MAX_JOB_COUNT_EXCEEDED",
    HTTP_400_BAD_REQUEST,
    "Max running job count for this type is exceeded.",
)

ERROR_JOB_NOT_CANCELLABLE = (
    "ERROR_JOB_NOT_CANCELLABLE",
    HTTP_400_BAD_REQUEST,
    "The job cannot be cancelled",
)
