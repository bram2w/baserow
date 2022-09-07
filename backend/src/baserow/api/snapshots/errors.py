from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND

ERROR_SNAPSHOT_DOES_NOT_EXIST = (
    "ERROR_SNAPSHOT_DOES_NOT_EXIST",
    HTTP_404_NOT_FOUND,
    "The requested snapshot does not exist.",
)

ERROR_MAXIMUM_SNAPSHOTS_REACHED = (
    "ERROR_MAXIMUM_SNAPSHOTS_REACHED",
    HTTP_400_BAD_REQUEST,
    "The group has already reached the snapshot limit.",
)

ERROR_SNAPSHOT_IS_BEING_CREATED = (
    "ERROR_SNAPSHOT_IS_BEING_CREATED",
    HTTP_400_BAD_REQUEST,
    "Snapshots creation is already in progress for the application.",
)

ERROR_SNAPSHOT_IS_BEING_RESTORED = (
    "ERROR_SNAPSHOT_IS_BEING_RESTORED",
    HTTP_400_BAD_REQUEST,
    "Snapshots can't be manipulated while being restored.",
)

ERROR_SNAPSHOT_IS_BEING_DELETED = (
    "ERROR_SNAPSHOT_IS_BEING_DELETED",
    HTTP_400_BAD_REQUEST,
    "Snapshots can't be manipulated while being deleted.",
)

ERROR_SNAPSHOT_NAME_NOT_UNIQUE = (
    "ERROR_SNAPSHOT_NAME_NOT_UNIQUE",
    HTTP_400_BAD_REQUEST,
    "Snapshots names must be unique per application.",
)

ERROR_SNAPSHOT_OPERATION_LIMIT_EXCEEDED = (
    "ERROR_SNAPSHOT_OPERATION_LIMIT_EXCEEDED",
    HTTP_400_BAD_REQUEST,
    "The limit of number of the same operation exceeded by the user.",
)
