from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND

ERROR_ROW_COMMENT_DOES_NOT_EXIST = (
    "ERROR_ROW_COMMENT_DOES_NOT_EXIST",
    HTTP_404_NOT_FOUND,
    "The requested row comment does not exist.",
)

ERROR_USER_NOT_COMMENT_AUTHOR = (
    "ERROR_USER_NOT_COMMENT_AUTHOR",
    HTTP_400_BAD_REQUEST,
    "The requesting user is not the author of the comment.",
)
