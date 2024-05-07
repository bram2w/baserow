from typing import Any, Dict, Optional, TypedDict

from rest_framework import serializers

from baserow.contrib.builder.elements.element_types import NavigationElementManager
from baserow.contrib.builder.elements.registries import CollectionFieldType
from baserow.contrib.builder.formula_importer import import_formula
from baserow.core.formula.serializers import FormulaSerializerField


class BooleanCollectionFieldType(CollectionFieldType):
    type = "boolean"
    allowed_fields = ["value"]
    serializer_field_names = ["value"]

    class SerializedDict(TypedDict):
        value: bool

    @property
    def serializer_field_overrides(self):
        return {
            "value": FormulaSerializerField(
                help_text="The boolean value.",
                required=False,
                allow_blank=True,
                default=False,
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

    @property
    def serializer_field_names(self):
        return (
            super().serializer_field_names
            + NavigationElementManager.serializer_field_names
            + [
                "link_name",
            ]
        )

    @property
    def allowed_fields(self):
        return (
            super().allowed_fields
            + NavigationElementManager.allowed_fields
            + [
                "link_name",
            ]
        )

    class SerializedDict(NavigationElementManager.SerializedDict):
        link_name: str

    @property
    def serializer_field_overrides(self):
        return (
            super().serializer_field_overrides
            | NavigationElementManager().get_serializer_field_overrides()
            | {
                "link_name": FormulaSerializerField(
                    help_text="The formula for the link name.",
                    required=False,
                    allow_blank=True,
                    default="",
                ),
            }
        )

    def deserialize_property(
        self,
        prop_name: str,
        value: Any,
        id_mapping: Dict[str, Any],
        data_source_id: Optional[int] = None,
    ) -> Any:
        if prop_name == "link_name" and data_source_id:
            return import_formula(value, id_mapping, data_source_id=data_source_id)

        return super().deserialize_property(
            prop_name,
            NavigationElementManager().deserialize_property(
                prop_name,
                value,
                id_mapping,
                data_source_id=data_source_id,
            ),
            id_mapping,
            data_source_id=data_source_id,
        )


class TagsCollectionFieldType(CollectionFieldType):
    type = "tags"
    allowed_fields = ["values", "colors", "colors_is_formula"]
    serializer_field_names = ["values", "colors", "colors_is_formula"]

    class SerializedDict(TypedDict):
        values: str
        colors: str
        colors_is_formula: bool

    @property
    def serializer_field_overrides(self):
        return {
            "values": FormulaSerializerField(
                help_text="The formula for the tags values",
                required=False,
                allow_blank=True,
                default="",
            ),
            "colors": serializers.CharField(
                help_text="The formula or value for the tags colors",
                required=False,
                allow_blank=True,
                default="",
            ),
            "colors_is_formula": serializers.BooleanField(
                required=False,
                default=False,
                help_text="Indicates whether the colors is a formula or not.",
            ),
        }

    def deserialize_property(
        self,
        prop_name: str,
        value: Any,
        id_mapping: Dict[str, Any],
        data_source_id: Optional[int] = None,
    ) -> Any:
        if prop_name in ["values", "colors"] and data_source_id:
            return import_formula(value, id_mapping, data_source_id=data_source_id)

        return super().deserialize_property(
            prop_name, value, id_mapping, data_source_id
        )
