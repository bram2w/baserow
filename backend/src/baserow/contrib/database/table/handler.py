from django.db import connections
from django.conf import settings

from baserow.core.exceptions import UserNotInGroupError
from baserow.core.utils import extract_allowed, set_allowed_attrs
from baserow.contrib.database.fields.models import TextField
from baserow.contrib.database.views.handler import ViewHandler
from baserow.contrib.database.views.view_types import GridViewType
from baserow.contrib.database.fields.handler import FieldHandler
from baserow.contrib.database.fields.field_types import TextFieldType, BooleanFieldType

from .models import Table
from .exceptions import TableDoesNotExist


class TableHandler:
    def get_table(self, user, table_id):
        """
        Selects a table with a given id from the database.

        :param user: The user on whose behalf the table is requested.
        :type user: User
        :param table_id: The identifier of the table that must be returned.
        :type table_id: int
        :return: The requested table of the provided id.
        :rtype: Table
        """

        try:
            table = Table.objects.select_related('database__group').get(id=table_id)
        except Table.DoesNotExist:
            raise TableDoesNotExist(f'The table with id {table_id} doe not exist.')

        group = table.database.group
        if not group.has_user(user):
            raise UserNotInGroupError(user, group)

        return table

    def create_table(self, user, database, fill_initial=False, **kwargs):
        """
        Creates a new table and a primary text field.

        :param user: The user on whose behalf the table is created.
        :type user: User
        :param database: The database that the table instance belongs to.
        :type database: Database
        :param fill_initial: Indicates whether an initial view, some fields and
            some rows should be added.
        :type fill_initial: bool
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

        if fill_initial:
            self.fill_initial_table_data(user, table)

        return table

    def fill_initial_table_data(self, user, table):
        """
        Fills the table with some initial data. A new table is expected that already
        has the a primary field named 'name'.

        :param user: The user on whose behalf the table is filled.
        :type: user: User
        :param table: The table that needs the initial data.
        :type table: User
        """

        view_handler = ViewHandler()
        field_handler = FieldHandler()

        view = view_handler.create_view(user, table, GridViewType.type, name='Grid')
        notes = field_handler.create_field(user, table, TextFieldType.type,
                                           name='Notes')
        active = field_handler.create_field(user, table, BooleanFieldType.type,
                                            name='Active')

        field_options = {
            notes.id: {'width': 400},
            active.id: {'width': 100}
        }
        fields = [notes, active]
        view_handler.update_grid_view_field_options(view, field_options, fields=fields)

        model = table.get_model(attribute_names=True)
        model.objects.create(name='Tesla', active=True)
        model.objects.create(name='Amazon', active=False)

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
