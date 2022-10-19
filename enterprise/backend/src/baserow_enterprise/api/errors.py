from rest_framework.status import HTTP_404_NOT_FOUND

ERROR_TEAM_DOES_NOT_EXIST = (
    "ERROR_TEAM_DOES_NOT_EXIST",
    HTTP_404_NOT_FOUND,
    "The requested team does not exist.",
)

ERROR_USER_NOT_IN_TEAM = "ERROR_USER_NOT_IN_TEAM"

ERROR_SUBJECT_DOES_NOT_EXIST = (
    "ERROR_SUBJECT_DOES_NOT_EXIST",
    HTTP_404_NOT_FOUND,
    "The requested subject does not exist.",
)
