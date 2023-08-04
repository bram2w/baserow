from django.utils.functional import lazy

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from baserow.contrib.builder.elements.models import Element
from baserow.contrib.builder.elements.registries import element_type_registry
from baserow.core.formula.serializers import FormulaSerializerField


class ElementSerializer(serializers.ModelSerializer):
    """
    Basic element serializer mostly for returned values.
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
            "style_padding_top",
            "style_padding_bottom",
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

    class Meta:
        model = Element
        fields = ("before_id", "type", "style_padding_top", "style_padding_bottom")


class UpdateElementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Element
        fields = ("style_padding_top", "style_padding_bottom")


class MoveElementSerializer(serializers.Serializer):
    before_id = serializers.IntegerField(
        allow_null=True,
        required=False,
        help_text=(
            "If provided, the element is moved before the element with this Id. "
            "Otherwise the element is placed at the end of the page."
        ),
    )


class PageParameterValueSerializer(serializers.Serializer):
    name = serializers.CharField()
    value = FormulaSerializerField(allow_blank=True)
