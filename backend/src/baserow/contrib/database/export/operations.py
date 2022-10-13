from baserow.contrib.database.table.operations import DatabaseTableOperationType


class ExportTableOperationType(DatabaseTableOperationType):
    type = "database.table.run_export"
