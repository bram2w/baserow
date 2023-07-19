from baserow.contrib.database.table.operations import DatabaseTableOperationType


class ReadRowCommentsOperationType(DatabaseTableOperationType):
    type = "database.table.list_comments"


class CreateRowCommentsOperationType(DatabaseTableOperationType):
    type = "database.table.create_comment"


class UpdateRowCommentsOperationType(DatabaseTableOperationType):
    type = "database.table.update_comment"


class DeleteRowCommentsOperationType(DatabaseTableOperationType):
    type = "database.table.delete_comment"


class RestoreRowCommentOperationType(DatabaseTableOperationType):
    type = "database.table.restore_comment"
