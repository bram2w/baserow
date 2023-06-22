from abc import ABC
from typing import Dict, Optional

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from baserow.api.user_files.serializers import UserFileSerializer
from baserow.contrib.builder.api.validators import image_file_id_validation
from baserow.contrib.builder.elements.models import (
    ALIGNMENTS,
    HeadingElement,
    ImageElement,
    LinkElement,
    ParagraphElement,
)
from baserow.contrib.builder.elements.registries import ElementType
from baserow.contrib.builder.elements.types import Expression
from baserow.contrib.builder.pages.handler import PageHandler
from baserow.contrib.builder.pages.models import Page
from baserow.contrib.builder.types import ElementDict
from baserow.core.user_files.models import UserFile


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
        from baserow.core.expression.serializers import ExpressionSerializer

        return {
            "value": ExpressionSerializer(
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
    PATH_PARAM_TYPE_TO_PYTHON_TYPE_MAP = {"text": str, "numeric": int}

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
            PageParameterValueSerializer,
        )
        from baserow.core.expression.serializers import ExpressionSerializer

        overrides = {
            "navigation_type": serializers.ChoiceField(
                choices=LinkElement.NAVIGATION_TYPES.choices,
                help_text=LinkElement._meta.get_field("navigation_type").help_text,
                required=False,
            ),
            "navigate_to_page_id": serializers.IntegerField(
                allow_null=True,
                default=None,
                help_text=LinkElement._meta.get_field("navigate_to_page").help_text,
                required=False,
            ),
            "navigate_to_url": ExpressionSerializer(
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
                choices=ALIGNMENTS.choices,
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

    def prepare_value_for_db(
        self, values: Dict, instance: Optional[LinkElement] = None
    ):
        page_params = values.get("page_parameters", [])
        navigate_to_page_id = values.get(
            "navigate_to_page_id", getattr(instance, "navigate_to_page_id", None)
        )

        if len(page_params) != 0 and navigate_to_page_id is not None:
            page = (
                PageHandler().get_page(navigate_to_page_id)
                if navigate_to_page_id is not None
                else instance.navigate_to_page
            )

            self._raise_if_path_params_are_invalid(page_params, page)

        return values

    def _raise_if_path_params_are_invalid(self, path_params: Dict, page: Page) -> None:
        """
        Checks if the path parameters being set are correctly correlated to the
        path parameters defined for the page.

        :param path_params: The path params defined for the navigation event
        :param page: The page the element is navigating to
        :raises ValidationError: If the param does not exist or the type does not match
        """

        parameter_types = {p["name"]: p["type"] for p in page.path_params}

        for page_parameter in path_params:
            page_parameter_name = page_parameter["name"]
            page_parameter_value = page_parameter["value"]
            page_parameter_type = parameter_types.get(page_parameter_name, None)

            if page_parameter_type is None:
                raise ValidationError(
                    f"Page path parameter {page_parameter} does not exist."
                )

            # We don't need to type check empty values since they can be used as
            # defaults for page parameters.
            if page_parameter_value is None or page_parameter_value == "":
                continue

            try:
                LinkElementType.PATH_PARAM_TYPE_TO_PYTHON_TYPE_MAP[page_parameter_type](
                    page_parameter_value
                )
            except (ValueError, TypeError):
                raise ValidationError(
                    f"'{page_parameter_value}' is not of type {page_parameter_type}"
                )


class ImageElementType(ElementType):
    """
    A simple image element that can display an image either through a remote source
    or via an uploaded file
    """

    type = "image"
    model_class = ImageElement
    serializer_field_names = [
        "image_source_type",
        "image_file",
        "image_url",
        "alt_text",
        "alignment",
    ]
    request_serializer_field_names = [
        "image_source_type",
        "image_file_id",
        "image_url",
        "alt_text",
        "alignment",
    ]
    allowed_fields = [
        "image_source_type",
        "image_file_id",
        "image_url",
        "alt_text",
        "alignment",
    ]

    class SerializedDict(ElementDict):
        image_source_type: str
        image_file: UserFile
        image_url: str
        alt_text: str

    def get_sample_params(self):
        return {
            "image_source_type": ImageElement.IMAGE_SOURCE_TYPES.UPLOAD,
            "image_file_id": None,
            "image_url": "https://test.com/image.png",
            "alt_text": "some alt text",
            "alignment": ALIGNMENTS.LEFT,
        }

    @property
    def serializer_field_overrides(self):
        overrides = {
            "image_file": UserFileSerializer(required=False),
        }

        overrides.update(super().serializer_field_overrides)
        return overrides

    @property
    def request_serializer_field_overrides(self):
        overrides = {
            "image_file_id": serializers.IntegerField(
                allow_null=True,
                required=False,
                help_text="The id of the image file",
                validators=[image_file_id_validation],
            ),
            "alignment": serializers.ChoiceField(
                choices=ALIGNMENTS.choices,
                help_text=ImageElement._meta.get_field("alignment").help_text,
                required=False,
            ),
        }
        if super().request_serializer_field_overrides is not None:
            overrides.update(super().request_serializer_field_overrides)
        return overrides
