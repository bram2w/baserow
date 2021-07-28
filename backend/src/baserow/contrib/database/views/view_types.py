from django.urls import path, include

from rest_framework.serializers import CharField

from baserow.api.user_files.serializers import UserFileField
from baserow.core.user_files.handler import UserFileHandler
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

    def export_serialized(self, grid, files_zip, storage):
        """
        Adds the serialized grid view options to the exported dict.
        """

        serialized = super().export_serialized(grid, files_zip, storage)

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

    def import_serialized(
        self, table, serialized_values, id_mapping, files_zip, storage
    ):
        """
        Imports the serialized grid view field options.
        """

        serialized_copy = serialized_values.copy()
        field_options = serialized_copy.pop("field_options")
        grid_view = super().import_serialized(
            table, serialized_copy, id_mapping, files_zip, storage
        )

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

    def export_serialized(self, form, files_zip, storage):
        """
        Adds the serialized form view options to the exported dict.
        """

        serialized = super().export_serialized(form, files_zip, storage)

        def add_user_file(user_file):
            if not user_file:
                return None

            name = user_file.name

            if name not in files_zip.namelist():
                file_path = UserFileHandler().user_file_path(name)
                with storage.open(file_path, mode="rb") as storage_file:
                    files_zip.writestr(name, storage_file.read())

            return {"name": name, "original_name": user_file.original_name}

        serialized["public"] = form.public
        serialized["title"] = form.title
        serialized["description"] = form.description
        serialized["cover_image"] = add_user_file(form.cover_image)
        serialized["logo_image"] = add_user_file(form.logo_image)
        serialized["submit_action"] = form.submit_action
        serialized["submit_action_message"] = form.submit_action_message
        serialized["submit_action_redirect_url"] = form.submit_action_redirect_url

        serialized_field_options = []
        for field_option in form.get_field_options():
            serialized_field_options.append(
                {
                    "id": field_option.id,
                    "field_id": field_option.field_id,
                    "name": field_option.name,
                    "description": field_option.description,
                    "enabled": field_option.enabled,
                    "required": field_option.required,
                    "order": field_option.order,
                }
            )

        serialized["field_options"] = serialized_field_options
        return serialized

    def import_serialized(
        self, table, serialized_values, id_mapping, files_zip, storage
    ):
        """
        Imports the serialized form view and field options.
        """

        def get_file(file):
            if not file:
                return None

            with files_zip.open(file["name"]) as stream:
                user_file = UserFileHandler().upload_user_file(
                    None, file["original_name"], stream, storage=storage
                )
            return user_file

        serialized_copy = serialized_values.copy()
        serialized_copy["cover_image"] = get_file(serialized_copy.pop("cover_image"))
        serialized_copy["logo_image"] = get_file(serialized_copy.pop("logo_image"))
        field_options = serialized_copy.pop("field_options")
        form_view = super().import_serialized(
            table, serialized_copy, id_mapping, files_zip, storage
        )

        if "database_form_view_field_options" not in id_mapping:
            id_mapping["database_form_view_field_options"] = {}

        for field_option in field_options:
            field_option_copy = field_option.copy()
            field_option_id = field_option_copy.pop("id")
            field_option_copy["field_id"] = id_mapping["database_fields"][
                field_option["field_id"]
            ]
            field_option_object = FormViewFieldOptions.objects.create(
                form_view=form_view, **field_option_copy
            )
            id_mapping["database_form_view_field_options"][
                field_option_id
            ] = field_option_object.id

        return form_view
