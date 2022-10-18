from baserow.contrib.database.operations import DatabaseOperationType


class ExportTableOperationType(DatabaseOperationType):
    type = "database.table.export.run"
