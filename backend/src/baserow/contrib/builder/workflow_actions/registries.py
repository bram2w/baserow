from typing import Any, Dict

from baserow.contrib.builder.registries import PublicCustomFieldsInstanceMixin
from baserow.contrib.builder.workflow_actions.models import BuilderWorkflowAction
from baserow.core.registry import (
    CustomFieldsRegistryMixin,
    ModelRegistryMixin,
    Registry,
)
from baserow.core.workflow_actions.registries import WorkflowActionType


class BuilderWorkflowActionType(WorkflowActionType, PublicCustomFieldsInstanceMixin):
    allowed_fields = ["page", "page_id", "element", "element_id", "event"]

    parent_property_name = "page"
    id_mapping_name = "builder_workflow_actions"

    def prepare_value_for_db(
        self, values: Dict, instance: BuilderWorkflowAction = None
    ):
        from baserow.contrib.builder.elements.handler import ElementHandler

        if "element_id" in values:
            values["element"] = ElementHandler().get_element(values["element_id"])

        return super().prepare_value_for_db(values, instance=instance)

    def deserialize_property(
        self, prop_name: str, value: Any, id_mapping: Dict[str, Any]
    ) -> Any:
        """
        This hooks allow to customize the deserialization of a property.

        :param prop_name: the name of the property being transformed.
        :param value: the value of this property.
        :param id_mapping: the id mapping dict.
        :return: the deserialized version for this property.
        """

        # Migrate page id
        if prop_name == "page_id":
            return id_mapping["builder_pages"][value]

        # Migrate element id
        if prop_name == "element_id":
            return id_mapping["builder_page_elements"][value]

        return value


class BuilderWorkflowActionTypeRegistry(
    Registry, ModelRegistryMixin, CustomFieldsRegistryMixin
):
    """
    Contains all the registered workflow action types for the builder module.
    """

    name = "builder_workflow_action_type"


builder_workflow_action_type_registry = BuilderWorkflowActionTypeRegistry()
