from django.urls import path, include

from rest_framework.serializers import PrimaryKeyRelatedField

from baserow.contrib.database.fields.models import SingleSelectField, FileField
from baserow.contrib.database.fields.exceptions import FieldNotInTable
from baserow.contrib.database.api.fields.errors import ERROR_FIELD_NOT_IN_TABLE
from baserow.contrib.database.views.registries import ViewType
from baserow_premium.api.views.kanban.serializers import (
    KanbanViewFieldOptionsSerializer,
)
from baserow_premium.api.views.kanban.errors import (
    ERROR_KANBAN_VIEW_FIELD_DOES_NOT_BELONG_TO_SAME_TABLE,
)

from .models import KanbanView, KanbanViewFieldOptions
from .exceptions import KanbanViewFieldDoesNotBelongToSameTable


class KanbanViewType(ViewType):
    type = "kanban"
    model_class = KanbanView
    field_options_model_class = KanbanViewFieldOptions
    field_options_serializer_class = KanbanViewFieldOptionsSerializer
    allowed_fields = ["single_select_field", "card_cover_image_field"]
    serializer_field_names = ["single_select_field", "card_cover_image_field"]
    serializer_field_overrides = {
        "single_select_field": PrimaryKeyRelatedField(
            queryset=SingleSelectField.objects.all(),
            required=False,
            default=None,
            allow_null=True,
        ),
        "card_cover_image_field": PrimaryKeyRelatedField(
            queryset=FileField.objects.all(),
            required=False,
            default=None,
            allow_null=True,
            help_text="References a file field of which the first image must be shown "
            "as card cover image.",
        ),
    }
    api_exceptions_map = {
        KanbanViewFieldDoesNotBelongToSameTable: (
            ERROR_KANBAN_VIEW_FIELD_DOES_NOT_BELONG_TO_SAME_TABLE
        ),
        FieldNotInTable: ERROR_FIELD_NOT_IN_TABLE,
    }

    def get_api_urls(self):
        from baserow_premium.api.views.kanban import urls as api_urls

        return [
            path("kanban/", include(api_urls, namespace=self.type)),
        ]

    def prepare_values(self, values, table, user):
        """
        Check if the provided single select option belongs to the same table.
        Check if the provided card cover image field belongs to the same table.
        """

        name = "single_select_field"
        if name in values:
            if isinstance(values[name], int):
                values[name] = SingleSelectField.objects.get(pk=values[name])

            if (
                isinstance(values[name], SingleSelectField)
                and values[name].table_id != table.id
            ):
                raise KanbanViewFieldDoesNotBelongToSameTable(
                    "The provided single select field does not belong to the kanban "
                    "view's table."
                )

        name = "card_cover_image_field"
        if name in values:
            if isinstance(values[name], int):
                values[name] = FileField.objects.get(pk=values[name])

            if (
                isinstance(values[name], FileField)
                and values[name].table_id != table.id
            ):
                raise FieldNotInTable(
                    "The provided file select field id does not belong to the kanban "
                    "view's table."
                )

        return values

    def export_serialized(self, kanban, files_zip, storage):
        """
        Adds the serialized kanban view options to the exported dict.
        """

        serialized = super().export_serialized(kanban, files_zip, storage)
        serialized["single_select_field_id"] = kanban.single_select_field_id

        serialized_field_options = []
        for field_option in kanban.get_field_options():
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
        Imports the serialized kanban view field options.
        """

        serialized_copy = serialized_values.copy()
        serialized_copy["single_select_field_id"] = id_mapping["database_fields"][
            serialized_copy.pop("single_select_field_id")
        ]
        field_options = serialized_copy.pop("field_options")
        kanban_view = super().import_serialized(
            table, serialized_copy, id_mapping, files_zip, storage
        )

        if "database_kanban_view_field_options" not in id_mapping:
            id_mapping["database_kanban_view_field_options"] = {}

        for field_option in field_options:
            field_option_copy = field_option.copy()
            field_option_id = field_option_copy.pop("id")
            field_option_copy["field_id"] = id_mapping["database_fields"][
                field_option["field_id"]
            ]
            field_option_object = KanbanViewFieldOptions.objects.create(
                kanban_view=kanban_view, **field_option_copy
            )
            id_mapping["database_kanban_view_field_options"][
                field_option_id
            ] = field_option_object.id

        return kanban_view

    def view_created(self, view):
        """
        When a kanban view is created, we want to set the first three fields as visible.
        """

        field_options = view.get_field_options(create_if_missing=True).order_by(
            "field__id"
        )
        ids_to_update = [f.id for f in field_options[0:3]]

        if len(ids_to_update) > 0:
            KanbanViewFieldOptions.objects.filter(id__in=ids_to_update).update(
                hidden=False
            )
