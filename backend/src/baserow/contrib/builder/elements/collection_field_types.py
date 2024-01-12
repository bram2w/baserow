from typing import Any, Dict, List, Optional, TypedDict

from rest_framework import serializers

from baserow.contrib.builder.api.elements.serializers import (
    PageParameterValueSerializer,
)
from baserow.contrib.builder.elements.models import LinkElement
from baserow.contrib.builder.elements.registries import CollectionFieldType
from baserow.contrib.builder.formula_importer import import_formula
from baserow.core.formula.serializers import FormulaSerializerField
from baserow.core.formula.types import BaserowFormula


class TextCollectionFieldType(CollectionFieldType):
    type = "text"
    allowed_fields = ["value"]
    serializer_field_names = ["value"]

    class SerializedDict(TypedDict):
        value: str

    @property
    def serializer_field_overrides(self):
        return {
            "value": FormulaSerializerField(
                help_text="The formula for the link URL.",
                required=False,
                allow_blank=True,
                default="",
            ),
        }

    def deserialize_property(
        self,
        prop_name: str,
        value: Any,
        id_mapping: Dict[str, Any],
        data_source_id: Optional[int] = None,
    ) -> Any:
        if prop_name == "value" and data_source_id:
            return import_formula(value, id_mapping, data_source_id=data_source_id)

        return super().deserialize_property(
            prop_name, value, id_mapping, data_source_id
        )


class LinkCollectionFieldType(CollectionFieldType):
    type = "link"
    allowed_fields = [
        "navigate_to_url",
        "navigation_type",
        "navigate_to_page_id",
        "link_name",
        "page_parameters",
    ]
    serializer_field_names = [
        "navigate_to_url",
        "navigation_type",
        "navigate_to_page_id",
        "link_name",
        "page_parameters",
    ]

    class SerializedDict(TypedDict):
        link_name: str
        page_parameters: List
        navigate_to_url: BaserowFormula
        navigation_type: str
        navigate_to_page_id: int

    @property
    def serializer_field_overrides(self):
        return {
            "link_name": FormulaSerializerField(
                help_text="The formula for the link name.",
                required=False,
                allow_blank=True,
                default="",
            ),
            "navigation_type": serializers.ChoiceField(
                choices=LinkElement.NAVIGATION_TYPES.choices,
                help_text="The link's navigation type.",
                required=False,
            ),
            "navigate_to_page_id": serializers.IntegerField(
                allow_null=True,
                default=None,
                help_text="Destination page id for this link. If null then we use the "
                "navigate_to_url property instead.",
                required=False,
            ),
            "navigate_to_url": FormulaSerializerField(
                help_text="The formula for the link URL.",
                default="",
                allow_blank=True,
                required=False,
            ),
            "page_parameters": PageParameterValueSerializer(
                many=True,
                help_text="The parameters for each parameters of the selected page if any.",
                required=False,
            ),
        }

    def deserialize_property(
        self,
        prop_name: str,
        value: Any,
        id_mapping: Dict[str, Any],
        data_source_id: Optional[int] = None,
    ) -> Any:
        if prop_name == "navigate_to_page_id" and value:
            return id_mapping["builder_pages"][value]

        if prop_name == "link_name" and data_source_id:
            return import_formula(value, id_mapping, data_source_id=data_source_id)

        if prop_name == "navigate_to_url" and data_source_id:
            return import_formula(value, id_mapping, data_source_id=data_source_id)

        if prop_name == "page_parameters" and data_source_id:
            return [
                {
                    **p,
                    "value": import_formula(
                        p["value"], id_mapping, data_source_id=data_source_id
                    ),
                }
                for p in value
            ]

        return super().deserialize_property(
            prop_name, value, id_mapping, data_source_id
        )
