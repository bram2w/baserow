from django.utils.functional import lazy

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from baserow.contrib.builder.api.workflow_actions.serializers import (
    BuilderWorkflowActionSerializer,
)
from baserow.contrib.builder.elements.models import CollectionElementField, Element
from baserow.contrib.builder.elements.registries import element_type_registry
from baserow.contrib.builder.elements.types import ElementsAndWorkflowActions
from baserow.contrib.builder.workflow_actions.registries import (
    builder_workflow_action_type_registry,
)
from baserow.core.formula.serializers import FormulaSerializerField


class ElementSerializer(serializers.ModelSerializer):
    """
    Basic element serializer mostly for returned values.

    👉 Mind to update the
    baserow.contrib.builder.api.domains.serializer.PublicElementSerializer
    when you update this one.
    """

    type = serializers.SerializerMethodField(help_text="The type of the element.")

    @extend_schema_field(OpenApiTypes.STR)
    def get_type(self, instance):
        return element_type_registry.get_by_model(instance.specific_class).type

    class Meta:
        model = Element
        fields = (
            "id",
            "page_id",
            "type",
            "order",
            "parent_element_id",
            "place_in_container",
            "style_border_top_color",
            "style_border_top_size",
            "style_padding_top",
            "style_border_bottom_color",
            "style_border_bottom_size",
            "style_padding_bottom",
            "style_background",
            "style_background_color",
            "style_width",
        )
        extra_kwargs = {
            "id": {"read_only": True},
            "page_id": {"read_only": True},
            "type": {"read_only": True},
            "order": {"read_only": True, "help_text": "Lowest first."},
        }


class CreateElementSerializer(serializers.ModelSerializer):
    """
    This serializer allow to set the type of an element and the element id before which
    we want to insert the new element.
    """

    type = serializers.ChoiceField(
        choices=lazy(element_type_registry.get_types, list)(),
        required=True,
        help_text="The type of the element.",
    )
    before_id = serializers.IntegerField(
        required=False,
        help_text="If provided, creates the element before the element with the "
        "given id.",
    )
    parent_element_id = serializers.IntegerField(
        allow_null=True,
        required=False,
        help_text="If provided, creates the element as a child of the element with "
        "the given id.",
    )

    class Meta:
        model = Element
        fields = (
            "order",
            "before_id",
            "type",
            "parent_element_id",
            "place_in_container",
            "style_border_top_color",
            "style_border_top_size",
            "style_padding_top",
            "style_border_bottom_color",
            "style_border_bottom_size",
            "style_padding_bottom",
            "style_background",
            "style_background_color",
            "style_width",
        )


class UpdateElementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Element
        fields = (
            "style_border_top_color",
            "style_border_top_size",
            "style_padding_top",
            "style_border_bottom_color",
            "style_border_bottom_size",
            "style_padding_bottom",
            "style_background",
            "style_background_color",
            "style_width",
        )


class MoveElementSerializer(serializers.Serializer):
    before_id = serializers.IntegerField(
        allow_null=True,
        required=False,
        help_text=(
            "If provided, the element is moved before the element with this Id. "
            "Otherwise the element is placed at the end of the page."
        ),
    )
    parent_element_id = serializers.IntegerField(
        allow_null=True,
        required=False,
        default=None,
        help_text="If provided, the element is moved as a child of the element with "
        "the given id.",
    )
    place_in_container = serializers.CharField(
        required=False,
        allow_null=True,
        default=None,
        help_text="The place in the container.",
    )


class DuplicateElementSerializer(serializers.Serializer):
    elements = serializers.SerializerMethodField(help_text="The duplicated elements.")
    workflow_actions = serializers.SerializerMethodField(
        help_text="The duplicated workflow actions"
    )

    @extend_schema_field(ElementSerializer(many=True))
    def get_elements(self, obj: ElementsAndWorkflowActions):
        return [
            element_type_registry.get_serializer(element, ElementSerializer).data
            for element in obj["elements"]
        ]

    @extend_schema_field(BuilderWorkflowActionSerializer(many=True))
    def get_workflow_actions(self, obj: ElementsAndWorkflowActions):
        return [
            builder_workflow_action_type_registry.get_serializer(
                workflow_action, BuilderWorkflowActionSerializer
            ).data
            for workflow_action in obj["workflow_actions"]
        ]


class PageParameterValueSerializer(serializers.Serializer):
    name = serializers.CharField()
    value = FormulaSerializerField(allow_blank=True)


class CollectionElementFieldSerializer(serializers.ModelSerializer):
    value = FormulaSerializerField(allow_blank=True)

    class Meta:
        model = CollectionElementField
        fields = (
            "id",
            "name",
            "value",
        )
