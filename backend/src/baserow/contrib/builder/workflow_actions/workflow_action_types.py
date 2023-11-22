from typing import Any, Dict

from baserow.contrib.builder.formula_importer import import_formula
from baserow.contrib.builder.workflow_actions.models import (
    NotificationWorkflowAction,
    OpenPageWorkflowAction,
)
from baserow.contrib.builder.workflow_actions.registries import (
    BuilderWorkflowActionType,
)
from baserow.contrib.builder.workflow_actions.types import BuilderWorkflowActionDict
from baserow.core.formula.serializers import FormulaSerializerField
from baserow.core.formula.types import BaserowFormula


class NotificationWorkflowActionType(BuilderWorkflowActionType):
    type = "notification"
    model_class = NotificationWorkflowAction
    serializer_field_names = ["title", "description"]
    serializer_field_overrides = {
        "title": FormulaSerializerField(
            help_text="The title of the notification. Must be an formula.",
            required=False,
            allow_blank=True,
            default="",
        ),
        "description": FormulaSerializerField(
            help_text="The description of the notification. Must be an formula.",
            required=False,
            allow_blank=True,
            default="",
        ),
    }

    class SerializedDict(BuilderWorkflowActionDict):
        title: BaserowFormula
        description: BaserowFormula

    @property
    def allowed_fields(self):
        return super().allowed_fields + ["title", "description"]

    def deserialize_property(self, prop_name, value, id_mapping: Dict) -> Any:
        """
        Migrate the formulas.
        """

        if prop_name == "title":
            return import_formula(value, id_mapping)

        if prop_name == "description":
            return import_formula(value, id_mapping)

        return super().deserialize_property(prop_name, value, id_mapping)

    def get_sample_params(self) -> Dict[str, Any]:
        return {"title": "'hello'", "description": "'there'"}


class OpenPageWorkflowActionType(BuilderWorkflowActionType):
    type = "open_page"
    model_class = OpenPageWorkflowAction
    serializer_field_names = ["url"]
    serializer_field_overrides = {
        "url": FormulaSerializerField(
            help_text="The url to open. Must be an formula.",
            required=False,
            allow_blank=True,
            default="",
        ),
    }

    class SerializedDict(BuilderWorkflowActionDict):
        url: BaserowFormula

    @property
    def allowed_fields(self):
        return super().allowed_fields + ["url"]

    def deserialize_property(self, prop_name, value, id_mapping: Dict) -> Any:
        """
        Migrate the formulas.
        """

        if prop_name == "url":
            return import_formula(value, id_mapping)

        if prop_name == "description":
            return import_formula(value, id_mapping)

        return super().deserialize_property(prop_name, value, id_mapping)

    def get_sample_params(self) -> Dict[str, Any]:
        return {"url": "'hello'"}
