from rest_framework.status import HTTP_404_NOT_FOUND

ERROR_WORKFLOW_ACTION_DOES_NOT_EXIST = (
    "ERROR_WORKFLOW_ACTION_DOES_NOT_EXIST",
    HTTP_404_NOT_FOUND,
    "The requested workflow action does not exist.",
)

ERROR_WORKFLOW_ACTION_NOT_IN_ELEMENT = (
    "ERROR_WORKFLOW_ACTION_NOT_IN_ELEMENT",
    HTTP_404_NOT_FOUND,
    "The requested workflow action does not belong to the element",
)
