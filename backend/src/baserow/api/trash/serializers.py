from distutils.util import strtobool

from django.utils.functional import lazy

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import fields, serializers

from baserow.api.mixins import UnknownFieldRaisesExceptionSerializerMixin
from baserow.core.models import Application, TrashEntry
from baserow.core.trash.registries import trash_item_type_registry


class TrashEntryRequestSerializer(
    UnknownFieldRaisesExceptionSerializerMixin, serializers.Serializer
):
    trash_item_id = serializers.IntegerField(min_value=0)
    parent_trash_item_id = serializers.IntegerField(
        min_value=0, required=False, allow_null=True
    )
    # GroupDeprecation
    trash_item_type = fields.ChoiceField(
        choices=lazy(trash_item_type_registry.get_types, list)(),
    )


class TrashStructureApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Application
        fields = ("id", "name", "trashed")


class TrashStructureGroupSerializer(serializers.Serializer):
    id = serializers.IntegerField(min_value=0)
    trashed = serializers.BooleanField()
    name = serializers.CharField()
    applications = TrashStructureApplicationSerializer(many=True)


class TrashStructureSerializer(serializers.Serializer):
    groups = TrashStructureGroupSerializer(
        many=True,
        source="workspaces",
        help_text="An array of group trash structure records. "
        "Deprecated, please use `workspaces`.",
    )  # GroupDeprecation
    workspaces = TrashStructureGroupSerializer(
        many=True, help_text="An array of " "workspace trash " "structure records"
    )


class TrashContentsSerializer(serializers.ModelSerializer):
    user_who_trashed = serializers.SerializerMethodField()
    trash_item_type = serializers.SerializerMethodField()
    group = serializers.IntegerField(source="group_id")  # GroupDeprecation

    @extend_schema_field(OpenApiTypes.STR)
    def get_user_who_trashed(self, instance):
        if instance.user_who_trashed is not None:
            return instance.user_who_trashed.first_name
        else:
            return None

    @extend_schema_field(OpenApiTypes.STR)
    def get_trash_item_type(self, instance) -> str:
        """
        If an API consumer hasn't yet adopted the "workspace"
        `trash_item_type`, give them the option to return "group"
        by testing the `respond_with_workspace_rename` querystring.
        """

        trash_item_type = instance.trash_item_type
        respond_with_workspace = bool(
            strtobool(
                self.context["request"].GET.get(
                    "respond_with_workspace_rename", "false"
                )
            )
        )
        if trash_item_type in ["group", "workspace"]:
            trash_item_type = "group"
            if respond_with_workspace:
                trash_item_type = "workspace"
        return trash_item_type

    class Meta:
        model = TrashEntry
        fields = (
            "id",
            "user_who_trashed",
            "trash_item_type",
            "trash_item_id",
            "parent_trash_item_id",
            "trashed_at",
            "application",
            "group",  # GroupDeprecation
            "workspace",
            "name",
            "names",
            "parent_name",
        )
