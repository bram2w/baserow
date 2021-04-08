from django.urls import path, include

from .registries import ViewType
from .models import GridView, GridViewFieldOptions


class GridViewType(ViewType):
    type = 'grid'
    model_class = GridView

    def get_api_urls(self):
        from baserow.contrib.database.api.views.grid import urls as api_urls

        return [
            path('grid/', include(api_urls, namespace=self.type)),
        ]

    def export_serialized(self, grid):
        """
        Adds the serialized grid view options to the exported dict.
        """

        serialized = super().export_serialized(grid)

        serialized_field_options = []
        for field_option in grid.get_field_options():
            serialized_field_options.append({
                'id': field_option.id,
                'field_id': field_option.field_id,
                'width': field_option.width,
                'hidden': field_option.hidden,
                'order': field_option.order
            })

        serialized['field_options'] = serialized_field_options
        return serialized

    def import_serialized(self, table, serialized_values, id_mapping):
        """
        Imports the serialized grid view field options.
        """

        serialized_copy = serialized_values.copy()
        field_options = serialized_copy.pop('field_options')
        grid_view = super().import_serialized(table, serialized_copy, id_mapping)

        if 'database_grid_view_field_options' not in id_mapping:
            id_mapping['database_grid_view_field_options'] = {}

        for field_option in field_options:
            field_option_copy = field_option.copy()
            field_option_id = field_option_copy.pop('id')
            field_option_copy['field_id'] = (
                id_mapping['database_fields'][field_option['field_id']]
            )
            field_option_object = GridViewFieldOptions.objects.create(
                grid_view=grid_view,
                **field_option_copy
            )
            id_mapping['database_grid_view_field_options'][field_option_id] = (
                field_option_object.id
            )

        return grid_view
