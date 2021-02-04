from baserow.ws.registries import PageType

from baserow.core.exceptions import UserNotInGroupError
from baserow.contrib.database.table.handler import TableHandler
from baserow.contrib.database.table.exceptions import TableDoesNotExist


class TablePageType(PageType):
    type = 'table'
    parameters = ['table_id']

    def can_add(self, user, web_socket_id, table_id, **kwargs):
        """
        The user should only have access to this page if the table exists and if he
        has access to the table.
        """

        if not table_id:
            return False

        try:
            handler = TableHandler()
            handler.get_table(user, table_id)
        except (UserNotInGroupError, TableDoesNotExist):
            return False

        return True

    def get_group_name(self, table_id, **kwargs):
        return f'table-{table_id}'
