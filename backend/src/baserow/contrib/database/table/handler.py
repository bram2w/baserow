from baserow.core.exceptions import UserNotInGroupError
from baserow.core.utils import extract_allowed, set_allowed_attrs

from .models import Table


class TableHandler:
    def create_table(self, user, database, **kwargs):
        """
        Creates a new table.

        :param user: The user on whose behalf the table is created.
        :type user: User
        :param database: The database that the table instance belongs to.
        :type database: Database
        :param kwargs: The fields that need to be set upon creation.
        :type kwargs: object
        :return: The created table instance.
        :rtype: Table
        """

        if not database.group.has_user(user):
            raise UserNotInGroupError(user, database.group)

        table_values = extract_allowed(kwargs, ['name'])
        last_order = Table.get_last_order(database)
        table = Table.objects.create(database=database, order=last_order,
                                     **table_values)

        return table

    def update_table(self, user, table, **kwargs):
        """
        Updates an existing table instance.

        :param user: The user on whose behalf the table is updated.
        :type user: User
        :param table: The table instance that needs to be updated.
        :type table: Table
        :param kwargs: The fields that need to be updated.
        :type kwargs: object
        :return: The updated table instance.
        :rtype: Table
        """

        if not isinstance(table, Table):
            raise ValueError('The table is not an instance of Table')

        if not table.database.group.has_user(user):
            raise UserNotInGroupError(user, table.database.group)

        table = set_allowed_attrs(kwargs, ['name'], table)
        table.save()

        return table

    def delete_table(self, user, table):
        """
        Deletes an existing table instance.

        :param user: The user on whose behalf the table is deleted.
        :type user: User
        :param table: The table instance that needs to be deleted.
        :type table: Table
        """

        if not isinstance(table, Table):
            raise ValueError('The table is not an instance of Table')

        if not table.database.group.has_user(user):
            raise UserNotInGroupError(user, table.database.group)

        table.delete()
