from baserow.contrib.database.table.models import Table


class TableFixtures:
    def create_database_table(self, user=None, **kwargs):
        if 'database' not in kwargs:
            kwargs['database'] = self.create_database_application(user=user)

        if 'name' not in kwargs:
            kwargs['name'] = self.fake.name()

        if 'order' not in kwargs:
            kwargs['order'] = 0

        return Table.objects.create(**kwargs)
