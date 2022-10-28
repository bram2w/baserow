from abc import ABCMeta

from baserow.core.registries import OperationType


class DatabaseOperationType(OperationType, metaclass=ABCMeta):
    context_scope_name = "database"


class ListTablesDatabaseTableOperationType(DatabaseOperationType):
    type = "database.list_tables"
    object_scope_name = "database_table"


class CreateTableDatabaseTableOperationType(DatabaseOperationType):
    type = "database.create_table"


class OrderTablesDatabaseTableOperationType(DatabaseOperationType):
    type = "database.order_tables"
    object_scope_name = "database_table"
