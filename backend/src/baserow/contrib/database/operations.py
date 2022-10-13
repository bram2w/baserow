from baserow.core.registries import OperationType


class DatabaseOperationType(OperationType):
    context_scope_name = "database"


class ReadDatabaseOperationType(DatabaseOperationType):
    type = "database.read"


class UpdateDatabaseOperationType(DatabaseOperationType):
    type = "database.update"


class DuplicateDatabaseOperationType(DatabaseOperationType):
    type = "database.duplicate"


class DeleteDatabaseOperationType(DatabaseOperationType):
    type = "database.delete"


class ListTablesDatabaseTableOperationType(DatabaseOperationType):
    type = "database.list_tables"
    object_scope_name = "database_table"


class CreateTableDatabaseTableOperationType(DatabaseOperationType):
    type = "database.create_table"


class OrderTablesDatabaseTableOperationType(DatabaseOperationType):
    type = "database.order_tables"
    object_scope_name = "database_table"
