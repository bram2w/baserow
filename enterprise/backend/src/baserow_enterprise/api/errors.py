from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND

ERROR_TEAM_NAME_NOT_UNIQUE = (
    "ERROR_TEAM_NAME_NOT_UNIQUE",
    HTTP_400_BAD_REQUEST,
    "The specified team name is already in use in this group.",
)

ERROR_TEAM_DOES_NOT_EXIST = (
    "ERROR_TEAM_DOES_NOT_EXIST",
    HTTP_404_NOT_FOUND,
    "The requested team does not exist.",
)

ERROR_SUBJECT_DOES_NOT_EXIST = (
    "ERROR_SUBJECT_DOES_NOT_EXIST",
    HTTP_404_NOT_FOUND,
    "The requested subject does not exist.",
)

ERROR_SUBJECT_TYPE_UNSUPPORTED = (
    "ERROR_SUBJECT_TYPE_UNSUPPORTED",
    HTTP_400_BAD_REQUEST,
    "The specified subject type is not supported.",
)

ERROR_SUBJECT_BAD_REQUEST = (
    "ERROR_SUBJECT_BAD_REQUEST",
    HTTP_400_BAD_REQUEST,
    "An ID or email address is required.",
)

ERROR_SUBJECT_NOT_IN_GROUP = (
    "ERROR_SUBJECT_NOT_IN_GROUP",
    HTTP_400_BAD_REQUEST,
    "The specified subject does not belong to this team's group.",
)

ERROR_ROLE_DOES_NOT_EXIST = (
    "ERROR_ROLE_DOES_NOT_EXIST",
    HTTP_404_NOT_FOUND,
    "The specified role does not exist.",
)
