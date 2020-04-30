from baserow.core.handler import CoreHandler
from baserow.core.registries import Plugin

from .table.handler import TableHandler
from .views.handler import ViewHandler
from .views.view_types import GridViewType
from .fields.handler import FieldHandler
from .fields.field_types import TextFieldType, BooleanFieldType


class DatabasePlugin(Plugin):
    type = 'database'

    def user_created(self, user, group):
        """
        This method is called when a new user is created. We are going to create a
        database, table, view, fields and some rows here as an example for the user.

        :param user: The newly created user.
        :param group: The newly created group for the user.
        """

        database = CoreHandler().create_application(user, group, type_name=self.type,
                                                    name=f"{user.first_name}'s company")

        table = TableHandler().create_table(user, database, name='Customers')
        ViewHandler().create_view(user, table, GridViewType.type, name='Grid')
        FieldHandler().create_field(user, table, TextFieldType.type, name='Last name')
        FieldHandler().create_field(user, table, BooleanFieldType.type, name='Active')
        model = table.get_model(attribute_names=True)
        model.objects.create(name='Elon', last_name='Musk', active=True)
        model.objects.create(name='Bill', last_name='Gates', active=False)
        model.objects.create(name='Mark', last_name='Zuckerburg', active=True)
        model.objects.create(name='Jeffrey', last_name='Bezos', active=True)

        table_2 = TableHandler().create_table(user, database, name='Projects')
        ViewHandler().create_view(user, table_2, GridViewType.type, name='Grid')
        FieldHandler().create_field(user, table_2, BooleanFieldType.type, name='Active')
        model = table_2.get_model(attribute_names=True)
        model.objects.create(name='Tesla', active=True)
        model.objects.create(name='SpaceX', active=False)
        model.objects.create(name='Amazon', active=False)
