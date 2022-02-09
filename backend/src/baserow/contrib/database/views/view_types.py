from django.urls import path, include
from rest_framework.serializers import PrimaryKeyRelatedField

from baserow.api.user_files.serializers import UserFileField
from baserow.contrib.database.api.views.form.errors import (
    ERROR_FORM_VIEW_FIELD_TYPE_IS_NOT_SUPPORTED,
)
from baserow.contrib.database.api.views.form.serializers import (
    FormViewFieldOptionsSerializer,
)
from baserow.contrib.database.api.views.gallery.serializers import (
    GalleryViewFieldOptionsSerializer,
)
from baserow.contrib.database.api.views.grid.serializers import (
    GridViewFieldOptionsSerializer,
)
from baserow.contrib.database.api.fields.errors import ERROR_FIELD_NOT_IN_TABLE
from baserow.contrib.database.fields.exceptions import FieldNotInTable
from baserow.contrib.database.fields.models import FileField
from baserow.contrib.database.fields.registries import field_type_registry
from baserow.core.user_files.handler import UserFileHandler
from .exceptions import FormViewFieldTypeIsNotSupported
from .handler import ViewHandler
from .models import (
    GridView,
    GridViewFieldOptions,
    GalleryView,
    GalleryViewFieldOptions,
    FormView,
    FormViewFieldOptions,
)
from .registries import ViewType


class GridViewType(ViewType):
    type = "grid"
    model_class = GridView
    field_options_model_class = GridViewFieldOptions
    field_options_serializer_class = GridViewFieldOptionsSerializer
    can_aggregate_field = True
    can_share = True
    when_shared_publicly_requires_realtime_events = True

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

    def get_visible_fields_and_model(self, view):
        """
        Returns the model and the field options in the correct order for exporting
        this view type.
        """

        grid_view = ViewHandler().get_view(view.id, view_model=GridView)

        ordered_visible_field_ids = self.get_visible_field_options_in_order(
            grid_view
        ).values_list("field__id", flat=True)
        model = grid_view.table.get_model(field_ids=ordered_visible_field_ids)
        ordered_field_objects = [
            model._field_objects[field_id] for field_id in ordered_visible_field_ids
        ]
        return ordered_field_objects, model

    def get_visible_field_options_in_order(self, grid_view):
        return (
            grid_view.get_field_options(create_if_missing=True)
            .filter(hidden=False)
            .order_by("-field__primary", "order", "field__id")
        )

    def get_hidden_field_options(self, grid_view):
        return grid_view.get_field_options(create_if_missing=False).filter(hidden=True)


class GalleryViewType(ViewType):
    type = "gallery"
    model_class = GalleryView
    field_options_model_class = GalleryViewFieldOptions
    field_options_serializer_class = GalleryViewFieldOptionsSerializer
    allowed_fields = ["card_cover_image_field"]
    serializer_field_names = ["card_cover_image_field"]
    serializer_field_overrides = {
        "card_cover_image_field": PrimaryKeyRelatedField(
            queryset=FileField.objects.all(),
            required=False,
            default=None,
            allow_null=True,
            help_text="References a file field of which the first image must be shown "
            "as card cover image.",
        )
    }
    api_exceptions_map = {
        FieldNotInTable: ERROR_FIELD_NOT_IN_TABLE,
    }

    def get_api_urls(self):
        from baserow.contrib.database.api.views.gallery import urls as api_urls

        return [
            path("gallery/", include(api_urls, namespace=self.type)),
        ]

    def prepare_values(self, values, table, user):
        """
        Check if the provided card cover image field belongs to the same table.
        """

        name = "card_cover_image_field"

        if name in values:
            if isinstance(values[name], int):
                values[name] = FileField.objects.get(pk=values[name])

            if (
                isinstance(values[name], FileField)
                and values[name].table_id != table.id
            ):
                raise FieldNotInTable(
                    "The provided file select field id does not belong to the gallery "
                    "view's table."
                )

        return values

    def export_serialized(self, gallery, files_zip, storage):
        """
        Adds the serialized gallery view options to the exported dict.
        """

        serialized = super().export_serialized(gallery, files_zip, storage)
        serialized_field_options = []
        for field_option in gallery.get_field_options():
            serialized_field_options.append(
                {
                    "id": field_option.id,
                    "field_id": field_option.field_id,
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
        Imports the serialized gallery view field options.
        """

        serialized_copy = serialized_values.copy()
        field_options = serialized_copy.pop("field_options")
        gallery_view = super().import_serialized(
            table, serialized_copy, id_mapping, files_zip, storage
        )

        if "database_gallery_view_field_options" not in id_mapping:
            id_mapping["database_gallery_view_field_options"] = {}

        for field_option in field_options:
            field_option_copy = field_option.copy()
            field_option_id = field_option_copy.pop("id")
            field_option_copy["field_id"] = id_mapping["database_fields"][
                field_option["field_id"]
            ]
            field_option_object = GalleryViewFieldOptions.objects.create(
                gallery_view=gallery_view, **field_option_copy
            )
            id_mapping["database_gallery_view_field_options"][
                field_option_id
            ] = field_option_object.id

        return gallery_view

    def view_created(self, view):
        """
        When a gallery view is created, we want to set the first three fields as
        visible.
        """

        field_options = view.get_field_options(create_if_missing=True).order_by(
            "field__id"
        )
        ids_to_update = [f.id for f in field_options[0:3]]

        if ids_to_update:
            GalleryViewFieldOptions.objects.filter(id__in=ids_to_update).update(
                hidden=False
            )


class FormViewType(ViewType):
    type = "form"
    model_class = FormView
    can_filter = False
    can_sort = False
    can_share = True
    restrict_link_row_public_view_sharing = False
    when_shared_publicly_requires_realtime_events = False
    field_options_model_class = FormViewFieldOptions
    field_options_serializer_class = FormViewFieldOptionsSerializer
    allowed_fields = [
        "title",
        "description",
        "cover_image",
        "logo_image",
        "submit_text",
        "submit_action",
        "submit_action_message",
        "submit_action_redirect_url",
    ]
    serializer_field_names = [
        "title",
        "description",
        "cover_image",
        "logo_image",
        "submit_text",
        "submit_action",
        "submit_action_message",
        "submit_action_redirect_url",
    ]
    serializer_field_overrides = {
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

        serialized["title"] = form.title
        serialized["description"] = form.description
        serialized["cover_image"] = add_user_file(form.cover_image)
        serialized["logo_image"] = add_user_file(form.logo_image)
        serialized["submit_text"] = form.submit_text
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

    def get_visible_field_options_in_order(self, form_view):
        return (
            form_view.get_field_options(create_if_missing=True)
            .filter(enabled=True)
            .order_by("-field__primary", "order", "field__id")
        )
