from django.contrib.auth.models import AbstractUser

from baserow.contrib.database.table.handler import TableHandler
from baserow.contrib.database.table.models import Table
from baserow.contrib.database.table.operations import ReadDatabaseTableOperationType
from baserow.core.handler import CoreHandler


class TableService:
    def __init__(self):
        self.handler = TableHandler()

    def get_table(self, user: AbstractUser, table_id: int) -> Table:
        """
        Returns a table instance from the database. Also checks the user
        permissions.

        :param user: The user trying to get the table.
        :param table_id: The ID of the table.
        :return: The table instance.
        """

        table = self.handler.get_table(table_id)

        CoreHandler().check_permissions(
            user,
            ReadDatabaseTableOperationType.type,
            workspace=table.database.workspace,
            context=table,
        )

        return table
