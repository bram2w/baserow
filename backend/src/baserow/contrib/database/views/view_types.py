from collections import defaultdict
from typing import Any, Dict, List, Optional, Set
from zipfile import ZipFile

from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.files.storage import Storage
from django.db.models import Q
from django.urls import include, path

from rest_framework.serializers import PrimaryKeyRelatedField

from baserow.api.user_files.serializers import UserFileField
from baserow.contrib.database.api.fields.errors import ERROR_FIELD_NOT_IN_TABLE
from baserow.contrib.database.api.views.form.errors import (
    ERROR_FORM_VIEW_FIELD_TYPE_IS_NOT_SUPPORTED,
)
from baserow.contrib.database.api.views.form.serializers import (
    FormViewFieldOptionsSerializer,
)
from baserow.contrib.database.api.views.gallery.serializers import (
    GalleryViewFieldOptionsSerializer,
)
from baserow.contrib.database.api.views.grid.errors import (
    ERROR_AGGREGATION_DOES_NOT_SUPPORTED_FIELD,
)
from baserow.contrib.database.api.views.grid.serializers import (
    GridViewFieldOptionsSerializer,
)
from baserow.contrib.database.fields.exceptions import FieldNotInTable
from baserow.contrib.database.fields.models import FileField
from baserow.contrib.database.fields.registries import field_type_registry
from baserow.contrib.database.table.models import Table
from baserow.contrib.database.views.registries import view_aggregation_type_registry
from baserow.core.user_files.handler import UserFileHandler
from baserow.core.user_files.models import UserFile

from .exceptions import (
    FormViewFieldTypeIsNotSupported,
    GridViewAggregationDoesNotSupportField,
)
from .handler import ViewHandler
from .models import (
    FormView,
    FormViewFieldOptions,
    FormViewFieldOptionsCondition,
    GalleryView,
    GalleryViewFieldOptions,
    GridView,
    GridViewFieldOptions,
    View,
)
from .registries import ViewType, form_view_mode_registry, view_filter_type_registry


class GridViewType(ViewType):
    type = "grid"
    model_class = GridView
    field_options_model_class = GridViewFieldOptions
    field_options_serializer_class = GridViewFieldOptionsSerializer
    can_aggregate_field = True
    can_share = True
    can_decorate = True
    has_public_info = True
    when_shared_publicly_requires_realtime_events = True
    allowed_fields = ["row_identifier_type"]
    field_options_allowed_fields = [
        "width",
        "hidden",
        "order",
        "aggregation_type",
        "aggregation_raw_type",
    ]
    serializer_field_names = ["row_identifier_type"]

    api_exceptions_map = {
        GridViewAggregationDoesNotSupportField: ERROR_AGGREGATION_DOES_NOT_SUPPORTED_FIELD,
    }

    def get_api_urls(self):
        from baserow.contrib.database.api.views.grid import urls as api_urls

        return [
            path("grid/", include(api_urls, namespace=self.type)),
        ]

    def export_serialized(
        self,
        grid: View,
        cache: Optional[Dict] = None,
        files_zip: Optional[ZipFile] = None,
        storage: Optional[Storage] = None,
    ):
        """
        Adds the serialized grid view options to the exported dict.
        """

        serialized = super().export_serialized(grid, cache, files_zip, storage)
        serialized["row_identifier_type"] = grid.row_identifier_type

        serialized_field_options = []
        for field_option in grid.get_field_options():
            serialized_field_options.append(
                {
                    "id": field_option.id,
                    "field_id": field_option.field_id,
                    "width": field_option.width,
                    "hidden": field_option.hidden,
                    "order": field_option.order,
                    "aggregation_type": field_option.aggregation_type,
                    "aggregation_raw_type": field_option.aggregation_raw_type,
                }
            )

        serialized["field_options"] = serialized_field_options
        return serialized

    def import_serialized(
        self,
        table: Table,
        serialized_values: Dict[str, Any],
        id_mapping: Dict[str, Any],
        files_zip: Optional[ZipFile] = None,
        storage: Optional[Storage] = None,
    ) -> Optional[View]:
        """
        Imports the serialized grid view field options.
        """

        serialized_copy = serialized_values.copy()
        field_options = serialized_copy.pop("field_options")
        grid_view = super().import_serialized(
            table, serialized_copy, id_mapping, files_zip, storage
        )
        if grid_view is not None:
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

    def before_field_options_update(self, view, field_options, fields):
        """
        Checks if a aggregation raw types are compatible with the field types.
        """

        fields_dict = {field.id: field for field in fields}

        for field_id, options in field_options.items():
            field = fields_dict.get(int(field_id), None)
            aggregation_raw_type = options.get("aggregation_raw_type")

            if aggregation_raw_type and field:

                try:
                    # Invalidate cache if new aggregation raw type has changed
                    prev_options = GridViewFieldOptions.objects.only(
                        "aggregation_raw_type"
                    ).get(field=field, grid_view=view)
                    if prev_options.aggregation_raw_type != aggregation_raw_type:
                        ViewHandler().clear_aggregation_cache(view, field.db_column)
                except GridViewFieldOptions.DoesNotExist:
                    pass

                # Checks if the aggregation raw type is compatible with the field type
                aggregation_type = view_aggregation_type_registry.get(
                    aggregation_raw_type
                )
                if not aggregation_type.field_is_compatible(field):
                    raise GridViewAggregationDoesNotSupportField(aggregation_type)

        return field_options

    def after_field_type_change(self, field):
        """
        Check field option aggregation_raw_type compatibility with the new field type.
        """

        field_options = (
            GridViewFieldOptions.objects_and_trash.filter(field=field)
            .exclude(aggregation_raw_type="")
            .select_related("grid_view")
        )

        view_handler = ViewHandler()

        for field_option in field_options:
            aggregation_type = view_aggregation_type_registry.get(
                field_option.aggregation_raw_type
            )

            view_handler.clear_aggregation_cache(
                field_option.grid_view, field.db_column
            )

            if not aggregation_type.field_is_compatible(field):
                # The field has an aggregation and the type is not compatible with
                # the new field, so we need to clean the aggregation.
                view_handler.update_field_options(
                    view=field_option.grid_view,
                    field_options={
                        field.id: {
                            "aggregation_type": "",
                            "aggregation_raw_type": "",
                        }
                    },
                )

    def get_visible_field_options_in_order(self, grid_view):
        return (
            grid_view.get_field_options(create_if_missing=True)
            .filter(hidden=False)
            .order_by("-field__primary", "order", "field__id")
        )

    def get_aggregations(self, grid_view):
        """
        Returns the (Field, aggregation_type) list computed from the field options for
        the specified view.
        """

        field_options = (
            GridViewFieldOptions.objects.filter(grid_view=grid_view)
            .exclude(aggregation_raw_type="")
            .select_related("field")
        )
        return [(option.field, option.aggregation_raw_type) for option in field_options]

    def after_field_value_update(self, updated_fields):
        """
        When a field value change, we need to invalidate the aggregation cache for this
        field.
        """

        to_clear = defaultdict(list)
        view_map = {}

        field_options = (
            GridViewFieldOptions.objects.filter(field__in=updated_fields)
            .exclude(aggregation_raw_type="")
            .select_related("grid_view", "field")
        )

        for options in field_options:
            to_clear[options.grid_view.id].append(options.field.db_column)
            view_map[options.grid_view.id] = options.grid_view

        view_handler = ViewHandler()
        for view_id, names in to_clear.items():
            view_handler.clear_aggregation_cache(view_map[view_id], names + ["total"])

    def after_field_update(self, updated_fields):
        """
        When a field configuration is changed, we need to invalid the cache for
        corresponding aggregations also.
        """

        self.after_field_value_update(updated_fields)

    def after_filter_update(self, grid_view):
        """
        If the view filters change we also need to invalid the aggregation cache for all
        fields of this view.
        """

        ViewHandler().clear_full_aggregation_cache(grid_view)

    def get_hidden_fields(
        self,
        view: GridView,
        field_ids_to_check: Optional[List[int]] = None,
    ) -> Set[int]:
        field_options = [o for o in view.gridviewfieldoptions_set.all() if o.hidden]
        if field_ids_to_check is not None:
            field_options = [
                o for o in field_options if o.field_id in field_ids_to_check
            ]
        return {o.field_id for o in field_options}

    def enhance_queryset(self, queryset):
        return queryset.prefetch_related("gridviewfieldoptions_set")


class GalleryViewType(ViewType):
    type = "gallery"
    model_class = GalleryView
    field_options_model_class = GalleryViewFieldOptions
    field_options_serializer_class = GalleryViewFieldOptionsSerializer
    allowed_fields = ["card_cover_image_field"]
    field_options_allowed_fields = ["hidden", "order"]
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
    can_decorate = True
    can_share = True
    has_public_info = True

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

    def export_serialized(
        self,
        gallery: View,
        cache: Optional[Dict] = None,
        files_zip: Optional[ZipFile] = None,
        storage: Optional[Storage] = None,
    ):
        """
        Adds the serialized gallery view options to the exported dict.
        """

        serialized = super().export_serialized(gallery, cache, files_zip, storage)

        if gallery.card_cover_image_field:
            serialized["card_cover_image_field_id"] = gallery.card_cover_image_field.id

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
        self,
        table: Table,
        serialized_values: Dict[str, Any],
        id_mapping: Dict[str, Any],
        files_zip: Optional[ZipFile] = None,
        storage: Optional[Storage] = None,
    ) -> Optional[View]:
        """
        Imports the serialized gallery view field options.
        """

        serialized_copy = serialized_values.copy()

        if serialized_copy.get("card_cover_image_field_id", None):
            serialized_copy["card_cover_image_field_id"] = id_mapping[
                "database_fields"
            ][serialized_copy["card_cover_image_field_id"]]

        field_options = serialized_copy.pop("field_options")

        gallery_view = super().import_serialized(
            table, serialized_copy, id_mapping, files_zip, storage
        )

        if gallery_view is not None:
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

    def export_prepared_values(self, view: GalleryView) -> Dict[str, Any]:
        """
        Add `card_cover_image_field` to the exportable fields.

        :param view: The gallery view to export.
        :return: The prepared values.
        """

        values = super().export_prepared_values(view)
        values["card_cover_image_field"] = view.card_cover_image_field_id

        return values

    def get_visible_field_options_in_order(self, gallery_view: GalleryView):
        return (
            gallery_view.get_field_options(create_if_missing=True)
            .filter(
                Q(hidden=False) | Q(field__id=gallery_view.card_cover_image_field_id)
            )
            .order_by("order", "field__id")
        )

    def get_hidden_fields(
        self,
        view: GalleryView,
        field_ids_to_check: Optional[List[int]] = None,
    ) -> Set[int]:
        hidden_field_ids = set()
        fields = view.table.field_set.all()
        field_options = view.galleryviewfieldoptions_set.all()

        if field_ids_to_check is not None:
            fields = [f for f in fields if f.id in field_ids_to_check]

        for field in fields:

            # The card cover image field is always visible.
            if field.id == view.card_cover_image_field_id:
                continue

            # Find corresponding field option
            field_option_matching = None
            for field_option in field_options:
                if field_option.field_id == field.id:
                    field_option_matching = field_option

            # A field is considered hidden, if it is explicitly hidden
            # or if the field options don't exist
            if field_option_matching is None or field_option_matching.hidden:
                hidden_field_ids.add(field.id)

        return hidden_field_ids

    def enhance_queryset(self, queryset):
        return queryset.prefetch_related("galleryviewfieldoptions_set")


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
        "mode",
        "cover_image",
        "logo_image",
        "submit_text",
        "submit_action",
        "submit_action_message",
        "submit_action_redirect_url",
    ]
    field_options_allowed_fields = [
        "name",
        "description",
        "enabled",
        "required",
        "show_when_matching_conditions",
        "condition_type",
        "order",
    ]
    serializer_field_names = [
        "title",
        "description",
        "mode",
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

    def after_field_type_change(self, field):
        field_type = field_type_registry.get_by_model(field)

        # If the new field type is not compatible with the form view, we must disable
        # all the form view field options because they're not compatible anymore.
        if not field_type.can_be_in_form_view:
            FormViewFieldOptions.objects_and_trash.filter(
                field=field, enabled=True
            ).update(enabled=False)

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

    def after_field_options_update(
        self, view, field_options, fields, update_field_option_instances
    ):
        """
        This method is called directly after the form view field options are updated.
        It will create, update or delete the provided conditions in a query efficient
        manner.
        """

        field_ids = [field.id for field in fields]
        updated_field_options_by_field_id = {
            o.field_id: o for o in update_field_option_instances
        }
        updated_field_options = [
            updated_field_options_by_field_id[field_id]
            for field_id, options in field_options.items()
            if "conditions" in options
        ]

        # Prefetch all the existing conditions to avoid N amount of queries later on.
        existing_conditions = {
            c.id: c
            for c in FormViewFieldOptionsCondition.objects.filter(
                field_option__in=updated_field_options,
            ).select_related("field_option")
        }

        conditions_to_create = []
        conditions_to_update = []
        condition_ids_to_delete = set(existing_conditions.keys())

        for field_id, options in field_options.items():
            if "conditions" not in options:
                continue

            numeric_field_id = int(field_id)
            updated_field_option_instance = updated_field_options_by_field_id[
                numeric_field_id
            ]

            for condition in options["conditions"]:
                if condition["field"] not in field_ids:
                    raise FieldNotInTable(
                        f"The field {condition['field']} does not belong to table "
                        f"{view.table.id}."
                    )

                # To avoid another query, we find the existing form condition in the
                # prefetched conditions.
                existing_condition = existing_conditions.get(condition["id"], None)
                if (
                    existing_condition is not None
                    and existing_condition.field_option.field_id == numeric_field_id
                ):
                    existing_condition.field_id = condition["field"]
                    existing_condition.type = condition["type"]
                    existing_condition.value = condition["value"]
                    conditions_to_update.append(existing_condition)
                    condition_ids_to_delete.remove(existing_condition.id)
                else:
                    conditions_to_create.append(
                        FormViewFieldOptionsCondition(
                            field_option=updated_field_option_instance,
                            field_id=condition["field"],
                            type=condition["type"],
                            value=condition["value"],
                        )
                    )

        if len(conditions_to_create) > 0:
            FormViewFieldOptionsCondition.objects.bulk_create(conditions_to_create)

        if len(conditions_to_update) > 0:
            FormViewFieldOptionsCondition.objects.bulk_update(
                conditions_to_update, ["field_id", "type", "value"]
            )

        if len(condition_ids_to_delete) > 0:
            FormViewFieldOptionsCondition.objects.filter(
                id__in=condition_ids_to_delete
            ).delete()

    def export_serialized(
        self,
        form: View,
        cache: Optional[Dict] = None,
        files_zip: Optional[ZipFile] = None,
        storage: Optional[Storage] = None,
    ):
        """
        Adds the serialized form view options to the exported dict.
        """

        serialized = super().export_serialized(form, cache, files_zip, storage)

        def add_user_file(user_file):
            if not user_file:
                return None

            name = user_file.name

            if files_zip is not None and name not in files_zip.namelist():
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
                    "show_when_matching_conditions": field_option.show_when_matching_conditions,
                    "condition_type": field_option.condition_type,
                    "conditions": [
                        {
                            "id": condition.id,
                            "field": condition.field_id,
                            "type": condition.type,
                            "value": view_filter_type_registry.get(
                                condition.type
                            ).get_export_serialized_value(condition.value, {}),
                        }
                        for condition in field_option.conditions.all()
                    ],
                }
            )

        serialized["field_options"] = serialized_field_options
        return serialized

    def import_serialized(
        self,
        table: Table,
        serialized_values: Dict[str, Any],
        id_mapping: Dict[str, Any],
        files_zip: Optional[ZipFile] = None,
        storage: Optional[Storage] = None,
    ) -> Optional[View]:
        """
        Imports the serialized form view and field options.
        """

        def get_file(file):
            if not file:
                return None

            if files_zip is None:
                user_file = UserFileHandler().get_user_file_by_name(file["name"])
            else:
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

        if form_view is not None:
            if "database_form_view_field_options" not in id_mapping:
                id_mapping["database_form_view_field_options"] = {}

            condition_objects = []
            for field_option in field_options:
                field_option_copy = field_option.copy()
                field_option_id = field_option_copy.pop("id")
                field_option_conditions = field_option_copy.pop("conditions", [])
                field_option_copy["field_id"] = id_mapping["database_fields"][
                    field_option["field_id"]
                ]
                field_option_object = FormViewFieldOptions.objects.create(
                    form_view=form_view, **field_option_copy
                )
                for condition in field_option_conditions:
                    value = view_filter_type_registry.get(
                        condition["type"]
                    ).set_import_serialized_value(condition["value"], id_mapping)
                    condition_objects.append(
                        FormViewFieldOptionsCondition(
                            field_option=field_option_object,
                            field_id=id_mapping["database_fields"][condition["field"]],
                            type=condition["type"],
                            value=value,
                        )
                    )
                id_mapping["database_form_view_field_options"][
                    field_option_id
                ] = field_option_object.id

        # Create the conditions in bulk to improve performance.
        FormViewFieldOptionsCondition.objects.bulk_create(condition_objects)

        return form_view

    def get_visible_field_options_in_order(self, form_view):
        return (
            form_view.get_field_options(create_if_missing=True)
            .filter(enabled=True)
            .order_by("-field__primary", "order", "field__id")
        )

    def before_view_create(self, values: dict, table: "Table", user: AbstractUser):
        if "mode" in values:
            mode_type = form_view_mode_registry.get(values["mode"])
        else:
            # This is the default mode that's set when nothing is provided.
            mode_type = form_view_mode_registry.get_default_type()

        mode_type.before_form_create(values, table, user)

    def before_view_update(self, values: dict, view: "View", user: AbstractUser):
        mode_type = form_view_mode_registry.get(values.get("mode", view.mode))
        mode_type.before_form_update(values, view, user)

    def prepare_values(
        self, values: Dict[str, Any], table: Table, user: AbstractUser
    ) -> Dict[str, Any]:
        """
        Prepares the values for the form view.
        If a serialized version of UserFile is found, it will be converted to a
        UserFile object.

        :param values: The values to prepare.
        :param table: The table the form view belongs to.
        :param user: The user that is submitting the form.
        :raises: ValidationError if the provided value for images is not
            compatible with UserFile.
        :return: The prepared values.
        """

        for user_file_key in ["cover_image", "logo_image"]:
            user_file = values.get(user_file_key, None)

            if user_file is None:
                continue

            if isinstance(user_file, dict):
                values[user_file_key] = UserFileHandler().get_user_file_by_name(
                    user_file.get("name", None)
                )

            elif not isinstance(user_file, UserFile):
                raise ValidationError(
                    f"Invalid user file type. '{user_file_key}' should be a UserFile \
                        instance or the serialized version of it."
                )

        return super().prepare_values(values, table, user)

    def export_prepared_values(self, view: FormView) -> Dict[str, Any]:
        """
        Add form fields to the exportable fields for undo/redo.
        This is the counterpart of prepare_values. Starting from object instances,
        it exports data to a serialized version of the object, in a way that
        prepare_values can be used to import it.

        :param view: The gallery view to export.
        :return: The prepared values.
        """

        values = super().export_prepared_values(view)

        for field in ["cover_image", "logo_image"]:
            user_file = getattr(view, field)
            values[field] = user_file and user_file.serialize()

        return values

    def enhance_queryset(self, queryset):
        return queryset.prefetch_related("formviewfieldoptions_set")

    def enhance_field_options_queryset(self, queryset):
        return queryset.prefetch_related("conditions")
