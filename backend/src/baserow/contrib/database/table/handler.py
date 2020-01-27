from django.db import connections
from django.conf import settings

from baserow.core.exceptions import UserNotInGroupError
from baserow.core.utils import extract_allowed, set_allowed_attrs
from baserow.contrib.database.fields.models import TextField

from .models import Table


class TableHandler:
    def create_table(self, user, database, **kwargs):
        """
        Creates a new table and a primary text field.

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

        # Create a primary text field for the table.
        TextField.objects.create(table=table, order=0, primary=True, name='Name')

        # Create the table schema in the database database.
        connection = connections[settings.USER_TABLE_DATABASE]
        with connection.schema_editor() as schema_editor:
            model = table.get_model()
            schema_editor.create_model(model)

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

        # Delete the table schema from the database.
        connection = connections[settings.USER_TABLE_DATABASE]
        with connection.schema_editor() as schema_editor:
            model = table.get_model()
            schema_editor.delete_model(model)

        table.delete()
