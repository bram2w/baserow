from typing import Any, Dict, TypedDict, Union

from rest_framework import serializers

from baserow.contrib.builder.elements.element_types import NavigationElementManager
from baserow.contrib.builder.elements.models import CollectionField
from baserow.contrib.builder.elements.registries import CollectionFieldType
from baserow.contrib.builder.formula_importer import import_formula
from baserow.contrib.builder.workflow_actions.models import BuilderWorkflowAction
from baserow.core.formula.serializers import (
    FormulaSerializerField,
    OptionalFormulaSerializerField,
)
from baserow.core.formula.types import BaserowFormula


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
        serialized_values: Dict[str, Any],
        **kwargs,
    ) -> Any:
        if prop_name == "value":
            return import_formula(value, id_mapping, **kwargs)

        return super().deserialize_property(
            prop_name, value, id_mapping, serialized_values, **kwargs
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
        serialized_values: Dict[str, Any],
        **kwargs,
    ) -> Any:
        if prop_name == "value":
            return import_formula(value, id_mapping, **kwargs)

        return super().deserialize_property(
            prop_name, value, id_mapping, serialized_values, **kwargs
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
        serialized_values: Dict[str, Any],
        **kwargs,
    ) -> Any:
        if prop_name == "link_name":
            return import_formula(value, id_mapping, **kwargs)

        return super().deserialize_property(
            prop_name,
            NavigationElementManager().deserialize_property(
                prop_name, value, id_mapping, **kwargs
            ),
            id_mapping,
            serialized_values,
            **kwargs,
        )


class TagsCollectionFieldType(CollectionFieldType):
    type = "tags"
    allowed_fields = ["values", "colors", "colors_is_formula"]
    serializer_field_names = ["values", "colors", "colors_is_formula"]

    class SerializedDict(TypedDict):
        values: str
        colors_is_formula: bool
        colors: Union[BaserowFormula, str]

    @property
    def serializer_field_overrides(self):
        return {
            "values": FormulaSerializerField(
                help_text="The formula for the tags values",
                required=False,
                allow_blank=True,
                default="",
            ),
            "colors": OptionalFormulaSerializerField(
                help_text="The formula or value for the tags colors",
                required=False,
                allow_blank=True,
                default="",
                is_formula_field_name="colors_is_formula",
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
        serialized_values: Dict[str, Any],
        **kwargs,
    ) -> Any:
        if prop_name == "values":
            return import_formula(value, id_mapping, **kwargs)

        if prop_name == "colors":
            return (
                import_formula(value, id_mapping, **kwargs)
                if serialized_values["config"]["colors_is_formula"]
                else value
            )

        return super().deserialize_property(
            prop_name, value, id_mapping, serialized_values, **kwargs
        )


class ButtonCollectionFieldType(CollectionFieldType):
    type = "button"
    allowed_fields = ["label"]
    serializer_field_names = ["label"]

    class SerializedDict(TypedDict):
        label: str

    @property
    def serializer_field_overrides(self):
        return {
            "label": FormulaSerializerField(
                help_text="The string value.",
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
        serialized_values: Dict[str, Any],
        **kwargs,
    ) -> Any:
        if prop_name == "label":
            return import_formula(value, id_mapping, **kwargs)

        return super().deserialize_property(
            prop_name, value, id_mapping, serialized_values, **kwargs
        )

    def before_delete(self, instance: CollectionField):
        # We delete the related workflow actions
        BuilderWorkflowAction.objects.filter(event__startswith=instance.uid).delete()
