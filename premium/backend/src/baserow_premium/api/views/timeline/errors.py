from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND

ERROR_TIMELINE_VIEW_HAS_INVALID_DATE_SETTINGS = (
    "ERROR_TIMELINE_VIEW_HAS_INVALID_DATE_SETTINGS",
    HTTP_400_BAD_REQUEST,
    "The requested timeline view does not have valid date settings. "
    "Please choose two valid date fields in the table that use the same ",
    "settings for 'include_time' and use the same timezone for all collaborators.",
)

ERROR_TIMELINE_DOES_NOT_EXIST = (
    "ERROR_TIMELINE_DOES_NOT_EXIST",
    HTTP_404_NOT_FOUND,
    "The requested timeline view does not exist.",
)
