"""
Shared helpers for the automation assistant tools.

Contains permission-checked accessors and the workflow creation orchestrator
used by ``tools.py`` and ``agents.py``.
"""

from typing import TYPE_CHECKING, Any

from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext as _

from baserow.contrib.automation.models import Automation
from baserow.contrib.automation.nodes.registries import automation_node_type_registry
from baserow.contrib.automation.nodes.service import AutomationNodeService
from baserow.contrib.automation.tools.nodes import nodes_in_order
from baserow.contrib.automation.tools.workflows import (
    get_automation_in_workspace,
    get_workflow_in_workspace,
)
from baserow.contrib.automation.workflows.models import AutomationWorkflow
from baserow.contrib.automation.workflows.service import AutomationWorkflowService
from baserow.core.models import Workspace
from baserow.core.tools import ToolContext

from .types import NodeUpdate, WorkflowCreate

if TYPE_CHECKING:
    from baserow_enterprise.assistant.deps import ToolHelpers

    from .types import ActionNodeCreate


def get_automation(
    automation_id: int, user: AbstractUser, workspace: Workspace
) -> Automation:
    """Fetch an automation scoped to the user's workspace."""

    return get_automation_in_workspace(ToolContext(user, workspace), automation_id)


def get_workflow(
    workflow_id: int, user: AbstractUser, workspace: Workspace
) -> AutomationWorkflow:
    """Fetch a workflow scoped to the user's workspace."""

    return get_workflow_in_workspace(ToolContext(user, workspace), workflow_id)


def get_nodes_in_order(user: AbstractUser, workflow: AutomationWorkflow) -> list[dict]:
    """Return the nodes of a workflow in execution order, with id, label and type."""

    return [
        {"id": node.id, "label": node.label, "type": node.get_type().type}
        for node, _previous, _output in nodes_in_order(user, workflow)
    ]


def add_nodes_to_workflow(
    user: AbstractUser,
    workflow: AutomationWorkflow,
    nodes: list["ActionNodeCreate"],
    tool_helpers: "ToolHelpers",
) -> tuple[list[Any], dict[int | str, Any]]:
    """
    Add action nodes to an existing workflow.

    The ``previous_node_ref`` on each node can reference:
    - An existing node ID as a string (e.g. "49")
    - A temp ref from an earlier node in the same ``nodes`` list

    Returns a list of created ORM nodes and the node mapping.
    """

    # Seed the mapping with existing nodes in the workflow
    existing_nodes = AutomationNodeService().get_nodes(user, workflow)
    node_mapping: dict[int | str, Any] = {}
    for n in existing_nodes:
        # Create a stub for the node_create part that has type and edges info
        stub = _ExistingNodeStub(n)
        node_mapping[str(n.id)] = (n, stub)
        node_mapping[n.id] = (n, stub)

    created = []
    for node in nodes:
        tool_helpers.raise_if_cancelled()
        reference_node_id, output = node.to_orm_reference_node(node_mapping)
        orm_node = _create_node(
            user,
            workflow,
            node,
            tool_helpers,
            reference_node_id=reference_node_id,
            output=output,
        )
        node_mapping[node.ref] = node_mapping[orm_node.id] = (orm_node, node)
        created.append(orm_node)

    return created, node_mapping


class _EdgeStub:
    """Bridges ORM edge ``uid`` to the ``_uid`` attribute expected by ``to_orm_reference_node``."""

    def __init__(self, orm_edge):
        self.label = orm_edge.label
        self._uid = str(orm_edge.uid)


class _ExistingNodeStub:
    """
    Lightweight stub exposing ``type`` and ``edges`` from an existing ORM node,
    so ``ActionNodeCreate.to_orm_reference_node`` can resolve router edge labels.
    """

    def __init__(self, orm_node):
        self.type = orm_node.get_type().type
        self.edges = []
        if self.type == "router" and hasattr(orm_node.service, "specific"):
            service = orm_node.service.specific
            if hasattr(service, "edges"):
                self.edges = [_EdgeStub(e) for e in service.edges.all()]


def create_workflow(
    user: AbstractUser,
    automation: Automation,
    workflow: "WorkflowCreate",
    tool_helpers: "ToolHelpers",
) -> tuple[AutomationWorkflow, dict[int | str, Any]]:
    """
    Create a workflow with its trigger and action nodes.

    Returns the ORM workflow and a mapping of ``{ref_or_id: (orm_node, node_create)}``
    for every created node, usable by downstream formula generation.
    """

    tool_helpers.update_status(
        _("Creating workflow '%(name)s'..." % {"name": workflow.name})
    )

    orm_wf = AutomationWorkflowService().create_workflow(
        user, automation.id, workflow.name
    )

    node_mapping: dict[int | str, Any] = {}

    # -- Trigger --
    orm_trigger = _create_node(user, orm_wf, workflow.trigger, tool_helpers)
    node_mapping[workflow.trigger.ref] = node_mapping[orm_trigger.id] = (
        orm_trigger,
        workflow.trigger,
    )

    # -- Action / router / iterator nodes --
    for node in workflow.nodes:
        try:
            reference_node_id, output = node.to_orm_reference_node(node_mapping)
        except ValueError as exc:
            from pydantic_ai import ModelRetry

            raise ModelRetry(str(exc)) from exc
        orm_node = _create_node(
            user,
            orm_wf,
            node,
            tool_helpers,
            reference_node_id=reference_node_id,
            output=output,
        )
        node_mapping[node.ref] = node_mapping[orm_node.id] = (orm_node, node)

    return orm_wf, node_mapping


def _create_node(user, workflow, node_create, tool_helpers, **extra_kwargs):
    """Create a single automation node (trigger or action)."""

    tool_helpers.update_status(
        _("Creating node '%(label)s'..." % {"label": node_create.label})
    )
    node_type = automation_node_type_registry.get(node_create.type)
    return AutomationNodeService().create_node(
        user,
        node_type,
        workflow,
        label=node_create.label,
        service=node_create.to_orm_service_dict(),
        **extra_kwargs,
    )


def update_node(
    user: "AbstractUser",
    workspace: "Workspace",
    node_update: "NodeUpdate",
    tool_helpers: "ToolHelpers",
):
    """
    Update an automation node's label and/or service config.

    :param user: The acting user.
    :param workspace: Workspace for permission check.
    :param node_update: The update definition.
    :param tool_helpers: Provides status updates.
    :returns: The updated ORM node.
    """

    node = AutomationNodeService().get_node(user, node_update.node_id)
    if node.workflow.automation.workspace_id != workspace.id:
        raise ValueError("Node not in workspace")

    kwargs = {}
    if node_update.label is not None:
        kwargs["label"] = node_update.label

    node_type = node.service.get_type().type if node.service else None
    service_dict = node_update.to_update_service_dict(node_type) if node_type else None
    if service_dict is not None:
        if (
            node_type == "local_baserow_upsert_row"
            and "table_id" in service_dict
            and service_dict["table_id"] != node.service.specific.table_id
        ):
            # Mappings from the previous table cannot be dispatched on the new one.
            service_dict["field_mappings"] = []
        kwargs["service"] = service_dict

    tool_helpers.update_status(
        _("Updating node '%(label)s'..." % {"label": node.label})
    )
    # Deferred row values still need update permission and test-clone invalidation.
    AutomationNodeService().update_node(user, node.id, **kwargs)

    return AutomationNodeService().get_node(user, node_update.node_id)


def delete_node(
    user: "AbstractUser",
    workspace: "Workspace",
    node_id: int,
):
    """
    Delete an automation node.

    :param user: The acting user.
    :param workspace: Workspace for permission check.
    :param node_id: ID of the node to delete.
    """

    node = AutomationNodeService().get_node(user, node_id)
    if node.workflow.automation.workspace_id != workspace.id:
        raise ValueError("Node not in workspace")
    AutomationNodeService().delete_node(user, node_id)
