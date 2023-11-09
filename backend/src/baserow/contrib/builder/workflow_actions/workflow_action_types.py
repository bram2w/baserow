from abc import abstractmethod
from typing import TYPE_CHECKING, Any, Dict

from baserow.contrib.builder.elements.handler import ElementHandler
from baserow.contrib.builder.formula_importer import import_formula
from baserow.contrib.builder.workflow_actions.models import (
    BuilderWorkflowAction,
    NotificationWorkflowAction,
    OpenPageWorkflowAction,
)
from baserow.contrib.builder.workflow_actions.types import BuilderWorkflowActionDict
from baserow.core.formula.serializers import FormulaSerializerField
from baserow.core.formula.types import BaserowFormula
from baserow.core.workflow_actions.registries import WorkflowActionType

if TYPE_CHECKING:
    from baserow.contrib.builder.pages.models import Page


class BuilderWorkflowActionType(WorkflowActionType):
    allowed_fields = ["page", "page_id", "element", "element_id", "event"]

    def prepare_value_for_db(
        self, values: Dict, instance: BuilderWorkflowAction = None
    ):
        if "element_id" in values:
            values["element"] = ElementHandler().get_element(values["element_id"])

        return super().prepare_value_for_db(values, instance=instance)

    @abstractmethod
    def get_sample_params(self) -> Dict[str, Any]:
        pass

    def import_serialized(
        self, page: "Page", serialized_values: Dict[str, Any], id_mapping: Dict
    ) -> BuilderWorkflowAction:
        if "builder_workflow_actions" not in id_mapping:
            id_mapping["builder_workflow_actions"] = {}

        serialized_copy = serialized_values.copy()

        # Remove extra keys
        workflow_action_id = serialized_copy.pop("id")
        serialized_copy.pop("type")

        # Convert table id
        serialized_copy["page_id"] = id_mapping["builder_pages"][
            serialized_copy["page_id"]
        ]

        # Convert element id
        if "element_id" in serialized_copy:
            serialized_copy["element_id"] = id_mapping["builder_page_elements"][
                serialized_copy["element_id"]
            ]

        workflow_action = self.model_class(page=page, **serialized_copy)
        workflow_action.save()

        id_mapping["builder_workflow_actions"][workflow_action_id] = workflow_action.id

        return workflow_action


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

    def import_serialized(
        self, page: "Page", serialized_values: Dict[str, Any], id_mapping: Dict
    ) -> BuilderWorkflowAction:
        """
        Migrate the formulas.
        """

        if "title" in serialized_values:
            serialized_values["title"] = import_formula(
                serialized_values["title"], id_mapping
            )

        if "description" in serialized_values:
            serialized_values["description"] = import_formula(
                serialized_values["description"], id_mapping
            )

        return super().import_serialized(page, serialized_values, id_mapping)

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

    def import_serialized(
        self, page: "Page", serialized_values: Dict[str, Any], id_mapping: Dict
    ) -> BuilderWorkflowAction:
        """
        Migrate the formulas.
        """

        if "url" in serialized_values:
            serialized_values["url"] = import_formula(
                serialized_values["url"], id_mapping
            )

        return super().import_serialized(page, serialized_values, id_mapping)

    def get_sample_params(self) -> Dict[str, Any]:
        return {"url": "'hello'"}
