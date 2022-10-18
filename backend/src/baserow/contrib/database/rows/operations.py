from baserow.contrib.database.operations import DatabaseOperationType


class DatabaseRowOperationType(DatabaseOperationType):
    context_scope_name = "database_row"


class ReadDatabaseRowOperationType(DatabaseRowOperationType):
    type = "database.table.read_row"


class UpdateDatabaseRowOperationType(DatabaseRowOperationType):
    type = "database.table.update_row"


class CreateDatabaseRowOperationType(DatabaseRowOperationType):
    type = "database.table.create_row"


class DeleteDatabaseRowOperationType(DatabaseRowOperationType):
    type = "database.table.delete_row"
