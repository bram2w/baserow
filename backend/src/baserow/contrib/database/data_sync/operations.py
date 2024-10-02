from baserow.contrib.database.table.operations import DatabaseTableOperationType


class SyncTableOperationType(DatabaseTableOperationType):
    type = "database.data_sync.sync_table"
