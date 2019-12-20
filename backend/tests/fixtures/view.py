from baserow.contrib.database.views.models import GridView


class ViewFixtures:
    def create_grid_view(self, user=None, **kwargs):
        if 'table' not in kwargs:
            kwargs['table'] = self.create_database_table(user=user)

        if 'name' not in kwargs:
            kwargs['name'] = self.fake.name()

        if 'order' not in kwargs:
            kwargs['order'] = 0

        return GridView.objects.create(**kwargs)
