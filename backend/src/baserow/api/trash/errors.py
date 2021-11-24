from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND

ERROR_TRASH_ITEM_DOES_NOT_EXIST = (
    "ERROR_TRASH_ITEM_DOES_NOT_EXIST",
    HTTP_404_NOT_FOUND,
    "The requested trash item does not exist.",
)

ERROR_CANNOT_RESTORE_PARENT_BEFORE_CHILD = (
    "ERROR_CANNOT_RESTORE_PARENT_BEFORE_CHILD",
    HTTP_400_BAD_REQUEST,
    "Cannot restore a trashed item if it's parent is also trashed, please restore the "
    "parent first.",
)

ERROR_PARENT_ID_MUST_BE_PROVIDED = (
    "ERROR_PARENT_ID_MUST_BE_PROVIDED",
    HTTP_400_BAD_REQUEST,
    "A parent id must be provided when using this trashable item type.",
)

ERROR_PARENT_ID_MUST_NOT_BE_PROVIDED = (
    "ERROR_PARENT_ID_MUST_NOT_BE_PROVIDED",
    HTTP_400_BAD_REQUEST,
    "A parent id must NOT be provided when using this trashable item type.",
)

ERROR_CANNOT_DELETE_ALREADY_DELETED_ITEM = (
    "ERROR_CANNOT_DELETE_ALREADY_DELETED_ITEM",
    HTTP_400_BAD_REQUEST,
    "This item has already been deleted.",
)
