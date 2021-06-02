from django.urls import path, include

from .handler import ViewHandler
from .models import GridView, GridViewFieldOptions
from .registries import ViewType


class GridViewType(ViewType):
    type = "grid"
    model_class = GridView

    def get_api_urls(self):
        from baserow.contrib.database.api.views.grid import urls as api_urls

        return [
            path("grid/", include(api_urls, namespace=self.type)),
        ]

    def export_serialized(self, grid):
        """
        Adds the serialized grid view options to the exported dict.
        """

        serialized = super().export_serialized(grid)

        serialized_field_options = []
        for field_option in grid.get_field_options():
            serialized_field_options.append(
                {
                    "id": field_option.id,
                    "field_id": field_option.field_id,
                    "width": field_option.width,
                    "hidden": field_option.hidden,
                    "order": field_option.order,
                }
            )

        serialized["field_options"] = serialized_field_options
        return serialized

    def import_serialized(self, table, serialized_values, id_mapping):
        """
        Imports the serialized grid view field options.
        """

        serialized_copy = serialized_values.copy()
        field_options = serialized_copy.pop("field_options")
        grid_view = super().import_serialized(table, serialized_copy, id_mapping)

        if "database_grid_view_field_options" not in id_mapping:
            id_mapping["database_grid_view_field_options"] = {}

        for field_option in field_options:
            field_option_copy = field_option.copy()
            field_option_id = field_option_copy.pop("id")
            field_option_copy["field_id"] = id_mapping["database_fields"][
                field_option["field_id"]
            ]
            field_option_object = GridViewFieldOptions.objects.create(
                grid_view=grid_view, **field_option_copy
            )
            id_mapping["database_grid_view_field_options"][
                field_option_id
            ] = field_option_object.id

        return grid_view

    def get_fields_and_model(self, view):
        """
        Returns the model and the field options in the correct order for exporting
        this view type.
        """

        grid_view = ViewHandler().get_view(view.id, view_model=GridView)

        ordered_field_objects = []
        ordered_visible_fields = (
            grid_view.get_field_options()
            .filter(hidden=False)
            .order_by("-field__primary", "order", "id")
            .values_list("field__id", flat=True)
        )
        model = view.table.get_model(field_ids=ordered_visible_fields)
        for field_id in ordered_visible_fields:
            ordered_field_objects.append(model._field_objects[field_id])
        return ordered_field_objects, model
