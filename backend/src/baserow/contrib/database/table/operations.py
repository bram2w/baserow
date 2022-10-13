from baserow.contrib.database.operations import DatabaseOperationType


class DatabaseTableOperationType(DatabaseOperationType):
    context_scope_name = "database_table"


class ReadDatabaseTableOperationType(DatabaseTableOperationType):
    type = "database.table.read"


class UpdateDatabaseTableOperationType(DatabaseTableOperationType):
    type = "database.table.update"


class DuplicateDatabaseTableOperationType(DatabaseTableOperationType):
    type = "database.table.duplicate"


class DeleteDatabaseTableOperationType(DatabaseTableOperationType):
    type = "database.table.delete"


class ListRowsDatabaseTableOperationType(DatabaseTableOperationType):
    type = "database.table.list_rows"
    object_scope_name = "database_row"


class CreateRowDatabaseTableOperationType(DatabaseTableOperationType):
    type = "database.table.create_row"
