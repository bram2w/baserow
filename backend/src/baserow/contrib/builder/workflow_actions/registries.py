from baserow.core.registry import (
    CustomFieldsRegistryMixin,
    ModelRegistryMixin,
    Registry,
)


class BuilderWorkflowActionTypeRegistry(
    Registry, ModelRegistryMixin, CustomFieldsRegistryMixin
):
    """
    Contains all the registered workflow action types for the builder module.
    """

    name = "builder_workflow_action_type"


builder_workflow_action_type_registry = BuilderWorkflowActionTypeRegistry()
