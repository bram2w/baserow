from baserow.contrib.database.table.operations import DatabaseTableOperationType


class ReadRowCommentsOperationType(DatabaseTableOperationType):
    type = "database.table.list_comments"


class CreateRowCommentsOperationType(DatabaseTableOperationType):
    type = "database.table.create_comment"
