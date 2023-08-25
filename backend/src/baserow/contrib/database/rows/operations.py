import abc

from baserow.contrib.database.operations import DatabaseOperationType


class DatabaseRowOperationType(DatabaseOperationType, abc.ABC):
    context_scope_name = "database_table"


class ReadDatabaseRowOperationType(DatabaseRowOperationType):
    type = "database.table.read_row"


class ReadAdjacentRowDatabaseRowOperationType(DatabaseRowOperationType):
    type = "database.table.read_adjacent_row"


class MoveRowDatabaseRowOperationType(DatabaseRowOperationType):
    type = "database.table.move_row"


class UpdateDatabaseRowOperationType(DatabaseRowOperationType):
    type = "database.table.update_row"


class DeleteDatabaseRowOperationType(DatabaseRowOperationType):
    type = "database.table.delete_row"


class RestoreDatabaseRowOperationType(DatabaseRowOperationType):
    type = "database.table.restore_row"


class ReadDatabaseRowHistoryOperationType(DatabaseRowOperationType):
    type = "database.table.read_row_history"
