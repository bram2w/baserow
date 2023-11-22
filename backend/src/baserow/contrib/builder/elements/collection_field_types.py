from typing import Any, Dict, Optional, TypedDict

from baserow.contrib.builder.elements.registries import CollectionFieldType
from baserow.contrib.builder.formula_importer import import_formula
from baserow.core.formula.serializers import FormulaSerializerField


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
    allowed_fields = ["url", "link_name"]
    serializer_field_names = ["url", "link_name"]

    class SerializedDict(TypedDict):
        url: str
        link_name: str

    @property
    def serializer_field_overrides(self):
        return {
            "url": FormulaSerializerField(
                help_text="The formula for the link URL.",
                required=False,
                allow_blank=True,
                default="",
            ),
            "link_name": FormulaSerializerField(
                help_text="The formula for the link name.",
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
        if prop_name in ["url", "link_name"] and data_source_id:
            return import_formula(value, id_mapping, data_source_id=data_source_id)

        return super().deserialize_property(
            prop_name, value, id_mapping, data_source_id
        )
