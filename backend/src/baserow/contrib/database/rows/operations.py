from baserow.contrib.database.operations import DatabaseOperationType


class DatabaseRowOperationType(DatabaseOperationType):
    context_scope_name = "database_row"


class ReadDatabaseRowOperationType(DatabaseRowOperationType):
    type = "database.table.row.read"


class UpdateDatabaseRowOperationType(DatabaseRowOperationType):
    type = "database.table.row.update"


class DeleteDatabaseRowOperationType(DatabaseRowOperationType):
    type = "database.table.row.delete"
