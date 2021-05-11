from baserow.contrib.database.fields.models import Field
from baserow.contrib.database.views.models import (
    GridView,
    GridViewFieldOptions,
    ViewFilter,
    ViewSort,
)


class ViewFixtures:
    def create_grid_view(self, user=None, **kwargs):
        if "table" not in kwargs:
            kwargs["table"] = self.create_database_table(user=user)

        if "name" not in kwargs:
            kwargs["name"] = self.fake.name()

        if "order" not in kwargs:
            kwargs["order"] = 0

        grid_view = GridView.objects.create(**kwargs)
        self.create_grid_view_field_options(grid_view)
        return grid_view

    def create_grid_view_field_options(self, grid_view, **kwargs):
        return [
            self.create_grid_view_field_option(grid_view, field, **kwargs)
            for field in Field.objects.filter(table=grid_view.table)
        ]

    def create_grid_view_field_option(self, grid_view, field, **kwargs):
        return GridViewFieldOptions.objects.create(
            grid_view=grid_view, field=field, **kwargs
        )

    def create_view_filter(self, user=None, **kwargs):
        if "view" not in kwargs:
            kwargs["view"] = self.create_grid_view(user)

        if "field" not in kwargs:
            kwargs["field"] = self.create_text_field(table=kwargs["view"].table)

        if "type" not in kwargs:
            kwargs["type"] = "equal"

        if "value" not in kwargs:
            kwargs["value"] = self.fake.name()

        return ViewFilter.objects.create(**kwargs)

    def create_view_sort(self, user=None, **kwargs):
        if "view" not in kwargs:
            kwargs["view"] = self.create_grid_view(user)

        if "field" not in kwargs:
            kwargs["field"] = self.create_text_field(table=kwargs["view"].table)

        if "order" not in kwargs:
            kwargs["order"] = "ASC"

        return ViewSort.objects.create(**kwargs)
