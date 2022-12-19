from baserow.contrib.database.rows.operations import (
    DeleteDatabaseRowOperationType,
    ReadDatabaseRowOperationType,
    UpdateDatabaseRowOperationType,
)
from baserow.contrib.database.table.operations import (
    CreateRowDatabaseTableOperationType,
)

TOKEN_OPERATION_TYPES = ["create", "read", "update", "delete"]

TOKEN_TO_OPERATION_MAP = {
    "create": CreateRowDatabaseTableOperationType.type,
    "read": ReadDatabaseRowOperationType.type,
    "update": UpdateDatabaseRowOperationType.type,
    "delete": DeleteDatabaseRowOperationType.type,
}

OPERATION_TO_TOKEN_MAP = {v: k for k, v in TOKEN_TO_OPERATION_MAP.items()}
