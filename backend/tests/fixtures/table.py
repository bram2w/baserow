from django.db import connection

from baserow.contrib.database.table.models import Table


class TableFixtures:
    def create_database_table(self, user=None, create_table=True, **kwargs):
        if 'database' not in kwargs:
            kwargs['database'] = self.create_database_application(user=user)

        if 'name' not in kwargs:
            kwargs['name'] = self.fake.name()

        if 'order' not in kwargs:
            kwargs['order'] = 0

        table = Table.objects.create(**kwargs)

        if create_table:
            with connection.schema_editor() as schema_editor:
                schema_editor.create_model(table.get_model())

        return table
