from django.urls import path, include

from rest_framework.serializers import CharField

from baserow.api.user_files.serializers import UserFileField
from baserow.contrib.database.api.views.form.errors import (
    ERROR_FORM_VIEW_FIELD_TYPE_IS_NOT_SUPPORTED,
)
from baserow.contrib.database.fields.registries import field_type_registry
from baserow.contrib.database.api.views.grid.serializers import (
    GridViewFieldOptionsSerializer,
)
from baserow.contrib.database.api.views.form.serializers import (
    FormViewFieldOptionsSerializer,
)

from .handler import ViewHandler
from .models import GridView, GridViewFieldOptions, FormView, FormViewFieldOptions
from .registries import ViewType
from .exceptions import FormViewFieldTypeIsNotSupported


class GridViewType(ViewType):
    type = "grid"
    model_class = GridView
    field_options_model_class = GridViewFieldOptions
    field_options_serializer_class = GridViewFieldOptionsSerializer

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


class FormViewType(ViewType):
    type = "form"
    model_class = FormView
    can_filter = False
    can_sort = False
    field_options_model_class = FormViewFieldOptions
    field_options_serializer_class = FormViewFieldOptionsSerializer
    allowed_fields = [
        "public",
        "title",
        "description",
        "cover_image",
        "logo_image",
        "submit_action",
        "submit_action_message",
        "submit_action_redirect_url",
    ]
    serializer_field_names = [
        "slug",
        "public",
        "title",
        "description",
        "cover_image",
        "logo_image",
        "submit_action",
        "submit_action_message",
        "submit_action_redirect_url",
    ]
    serializer_field_overrides = {
        "slug": CharField(
            read_only=True,
            help_text="The unique slug that can be used to construct a public URL.",
        ),
        "cover_image": UserFileField(
            required=False,
            help_text="The cover image that must be displayed at the top of the form.",
        ),
        "logo_image": UserFileField(
            required=False,
            help_text="The logo image that must be displayed at the top of the form.",
        ),
    }
    api_exceptions_map = {
        FormViewFieldTypeIsNotSupported: ERROR_FORM_VIEW_FIELD_TYPE_IS_NOT_SUPPORTED,
    }

    def get_api_urls(self):
        from baserow.contrib.database.api.views.form import urls as api_urls

        return [
            path("form/", include(api_urls, namespace=self.type)),
        ]

    def before_field_options_update(self, view, field_options, fields):
        """
        Checks if a field type that is incompatible with the form view is being
        enabled.
        """

        fields_dict = {field.id: field for field in fields}
        for field_id, options in field_options.items():
            field = fields_dict.get(int(field_id), None)
            if options.get("enabled") and field:
                field_type = field_type_registry.get_by_model(field.specific_class)
                if not field_type.can_be_in_form_view:
                    raise FormViewFieldTypeIsNotSupported(field_type.type)

        return field_options
