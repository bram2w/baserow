from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND


ERROR_AIRTABLE_IMPORT_JOB_DOES_NOT_EXIST = (
    "ERROR_AIRTABLE_IMPORT_JOB_DOES_NOT_EXIST",
    HTTP_404_NOT_FOUND,
    "The requested Airtable import job does not exist.",
)
ERROR_AIRTABLE_JOB_ALREADY_RUNNING = (
    "ERROR_AIRTABLE_JOB_ALREADY_RUNNING",
    HTTP_400_BAD_REQUEST,
    "Another Airtable import job is already running for you.",
)
