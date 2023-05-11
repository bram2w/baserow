from abc import ABC

from rest_framework import serializers

from baserow.contrib.builder.elements.models import (
    HeadingElement,
    LinkElement,
    ParagraphElement,
)
from baserow.contrib.builder.elements.registries import ElementType
from baserow.contrib.builder.elements.types import Expression
from baserow.contrib.builder.types import ElementDict


class BaseTextElementType(ElementType, ABC):
    """
    Base class for text elements.
    """

    serializer_field_names = ["value"]
    allowed_fields = ["value"]

    class SerializedDict(ElementDict):
        value: Expression

    @property
    def serializer_field_overrides(self):
        from baserow.contrib.builder.api.elements.serializers import ExpressionField

        return {
            "value": ExpressionField(
                help_text="The value of the element. Must be an expression.",
                required=False,
                allow_blank=True,
                default="",
            ),
        }


class HeadingElementType(BaseTextElementType):
    """
    A simple heading element that can be used to display a title.
    """

    type = "heading"
    model_class = HeadingElement

    class SerializedDict(ElementDict):
        value: Expression
        level: int

    @property
    def serializer_field_names(self):
        return super().serializer_field_names + ["level"]

    @property
    def allowed_fields(self):
        return super().allowed_fields + ["level"]

    @property
    def serializer_field_overrides(self):
        overrides = {
            "level": serializers.IntegerField(
                help_text="The level of the heading from 1 to 6.",
                min_value=1,
                max_value=6,
                default=1,
            )
        }
        overrides.update(super().serializer_field_overrides)
        return overrides

    def get_sample_params(self):
        return {
            "value": "Corporis perspiciatis",
            "level": 2,
        }


class ParagraphElementType(BaseTextElementType):
    """
    A simple paragraph element that can be used to display a paragraph of text.
    """

    type = "paragraph"
    model_class = ParagraphElement

    def get_sample_params(self):
        return {
            "value": "Suscipit maxime eos ea vel commodi dolore. "
            "Eum dicta sit rerum animi. Sint sapiente eum cupiditate nobis vel. "
            "Maxime qui nam consequatur. "
            "Asperiores corporis perspiciatis nam harum veritatis. "
            "Impedit qui maxime aut illo quod ea molestias."
        }


class LinkElementType(BaseTextElementType):
    """
    A simple paragraph element that can be used to display a paragraph of text.
    """

    type = "link"
    model_class = LinkElement

    class SerializedDict(ElementDict):
        value: Expression
        destination: Expression
        open_new_tab: bool

    @property
    def serializer_field_names(self):
        return super().serializer_field_names + [
            "navigation_type",
            "navigate_to_page_id",
            "navigate_to_url",
            "page_parameters",
            "variant",
            "target",
            "width",
            "alignment",
        ]

    @property
    def allowed_fields(self):
        return super().allowed_fields + [
            "navigation_type",
            "navigate_to_page_id",
            "navigate_to_url",
            "page_parameters",
            "variant",
            "target",
            "width",
            "alignment",
        ]

    def import_serialized(self, page, serialized_values, id_mapping):
        serialized_copy = serialized_values.copy()
        if serialized_copy["navigate_to_page_id"]:
            serialized_copy["navigate_to_page_id"] = id_mapping["builder_pages"][
                serialized_copy["navigate_to_page_id"]
            ]
        return super().import_serialized(page, serialized_copy, id_mapping)

    @property
    def serializer_field_overrides(self):
        from baserow.contrib.builder.api.elements.serializers import (
            ExpressionField,
            PageParameterValueSerializer,
        )

        overrides = {
            "navigation_type": serializers.ChoiceField(
                choices=LinkElement.NAVIGATION_TYPES.choices,
                help_text=LinkElement._meta.get_field("navigation_type").help_text,
                required=False,
            ),
            "navigate_to_page_id": serializers.IntegerField(
                allow_null=True,
                help_text=LinkElement._meta.get_field("navigate_to_page").help_text,
                required=False,
            ),
            "navigate_to_url": ExpressionField(
                help_text=LinkElement._meta.get_field("navigate_to_url").help_text,
                default="",
                allow_blank=True,
                required=False,
            ),
            "page_parameters": PageParameterValueSerializer(
                many=True,
                help_text=LinkElement._meta.get_field("navigate_to_url").help_text,
                required=False,
            ),
            "variant": serializers.ChoiceField(
                choices=LinkElement.VARIANTS.choices,
                help_text=LinkElement._meta.get_field("variant").help_text,
                required=False,
            ),
            "target": serializers.ChoiceField(
                choices=LinkElement.TARGETS.choices,
                help_text=LinkElement._meta.get_field("target").help_text,
                required=False,
            ),
            "width": serializers.ChoiceField(
                choices=LinkElement.WIDTHS.choices,
                help_text=LinkElement._meta.get_field("width").help_text,
                required=False,
            ),
            "alignment": serializers.ChoiceField(
                choices=LinkElement.ALIGNMENTS.choices,
                help_text=LinkElement._meta.get_field("alignment").help_text,
                required=False,
            ),
        }
        overrides.update(super().serializer_field_overrides)
        return overrides

    def get_sample_params(self):
        return {
            "navigation_type": "custom",
            "navigate_to_page_id": None,
            "navigate_to_url": "http://example.com",
            "page_parameters": [],
            "variant": "link",
            "target": "blank",
            "width": "auto",
            "alignment": "center",
        }
