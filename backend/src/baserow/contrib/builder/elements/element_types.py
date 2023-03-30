from abc import ABC

from rest_framework import serializers

from baserow.contrib.builder.elements.models import HeadingElement, ParagraphElement
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
