from django.urls import path, include

from baserow.core.handler import CoreHandler
from baserow.core.registries import ApplicationType

from .models import Database
from .table.handler import TableHandler
from .views.handler import ViewHandler
from .views.view_types import GridViewType
from .fields.handler import FieldHandler
from .fields.field_types import TextFieldType, BooleanFieldType
from .api.v0 import urls as api_urls
from .api.v0.serializers import DatabaseSerializer


class DatabaseApplicationType(ApplicationType):
    type = 'database'
    model_class = Database
    instance_serializer_class = DatabaseSerializer

    def user_created(self, user, group):
        """
        This method is called when a new user is created. We are going to create a
        database, table, view, fields and some rows here as an example for the user.

        :param user: The newly created user.
        :param group: The newly created group for the user.
        """

        database = CoreHandler().create_application(user, group, type_name=self.type,
                                                    name='Company')
        table = TableHandler().create_table(user, database, name='Customers')
        ViewHandler().create_view(user, table, GridViewType.type, name='Grid')
        FieldHandler().create_field(user, table, TextFieldType.type, name='Last name')
        FieldHandler().create_field(user, table, BooleanFieldType.type, name='Active')

        model = table.get_model(attribute_names=True)
        model.objects.create(name='Elon', last_name='Musk', active=True)
        model.objects.create(name='Bill', last_name='Gates', active=False)
        model.objects.create(name='Mark', last_name='Zuckerburg', active=True)
        model.objects.create(name='Jeffrey', last_name='Bezos', active=True)

    def pre_delete(self, user, database):
        """
        When a database is deleted we must also delete the related tables via the table
        handler.
        """
        database_tables = database.table_set.all().select_related('database__group')
        table_handler = TableHandler()

        for table in database_tables:
            table_handler.delete_table(user, table)

    def get_api_v0_urls(self):
        return [
            path('database/', include(api_urls, namespace=self.type)),
        ]
