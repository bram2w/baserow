"""
Node tools shared by the clients that act for a user.
"""

from typing import Annotated, Any

from django.contrib.auth.models import AbstractUser

from pydantic import Field

from baserow.contrib.automation.nodes.handler import AutomationNodeHandler
from baserow.contrib.automation.nodes.models import AutomationNode
from baserow.contrib.automation.nodes.operations import (
    ReadAutomationNodeOperationType,
)
from baserow.contrib.automation.nodes.service import AutomationNodeService
from baserow.contrib.automation.tools.workflows import get_workflow_in_workspace
from baserow.contrib.automation.workflows.models import AutomationWorkflow
from baserow.core.handler import CoreHandler
from baserow.core.tools import ToolContext


def get_node_in_workspace(ctx: ToolContext, node_id: int) -> AutomationNode:
    """
    Get a node of a workflow in the context's workspace.

    :raises AutomationNodeDoesNotExist: When the node is missing, trashed or in
        another workspace.
    :raises PermissionException: When the user may not read it.
    """

    node = AutomationNodeHandler().get_node(
        node_id,
        base_queryset=AutomationNode.objects.filter(
            workflow__automation__workspace=ctx.workspace
        ),
    )
    CoreHandler().check_permissions(
        ctx.user,
        ReadAutomationNodeOperationType.type,
        workspace=ctx.workspace,
        context=node,
    )
    return node


def _child_ids(info: dict[str, Any]) -> list[int]:
    children = info.get("children")
    if isinstance(children, dict):
        return [node_id for ids in children.values() for node_id in ids]
    return list(children) if isinstance(children, list) else []


def nodes_in_order(
    user: AbstractUser, workflow: AutomationWorkflow
) -> list[tuple[AutomationNode, AutomationNode | None, str]]:
    """
    The nodes of a workflow in execution order: the trigger, then each node after
    the one before it, a container's children before the nodes that follow it.

    :returns: Each node with the node it follows (None for the trigger) and the
        output of that node it is attached to ("" for the default one).
    """

    nodes = {
        node.id: node for node in AutomationNodeService().get_nodes(user, workflow)
    }
    graph = workflow.get_graph().graph
    ordered: list[tuple[AutomationNode, AutomationNode | None, str]] = []
    visited: set[int] = set()

    def walk(node_id: int, previous: AutomationNode | None, output: str) -> None:
        if node_id in visited or node_id not in nodes:
            return
        visited.add(node_id)
        node = nodes[node_id]
        ordered.append((node, previous, output))
        info = graph.get(str(node_id), {})
        for child_id in _child_ids(info):
            walk(child_id, node, "")
        # A router's branches in their order, the default one last, as the editor
        # shows them.
        branch_order = [edge["uid"] for edge in router_edges(node)] + [""]
        next_outputs = sorted(
            info.get("next", {}).items(),
            key=lambda item: (
                branch_order.index(item[0]) if item[0] in branch_order else 0
            ),
        )
        for next_output, next_ids in next_outputs:
            for next_id in next_ids:
                walk(next_id, node, next_output)

    trigger_id = graph.get("0")
    if trigger_id is not None:
        walk(trigger_id, None, "")
    return ordered


def router_edges(node: AutomationNode) -> list[dict[str, str]]:
    """The branches of a router node in order, empty for other nodes."""

    if node.get_type().type != "router":
        return []
    return [
        {"label": edge.label, "uid": str(edge.uid)}
        for edge in node.service.specific.edges.all()
    ]


def _compact_properties(schema: dict[str, Any]) -> dict[str, Any]:
    properties = {}
    for key, prop in (schema.get("properties") or {}).items():
        entry = {"title": prop.get("title", key), "type": prop.get("type")}
        if prop.get("type") == "object" and prop.get("properties"):
            entry["properties"] = _compact_properties(prop)
        elif prop.get("type") == "array" and isinstance(prop.get("items"), dict):
            items = prop["items"]
            if items.get("properties"):
                entry["items"] = _compact_properties(items)
        properties[key] = entry
    return properties


def output_schema(node: AutomationNode) -> dict[str, Any]:
    """
    What a node outputs, for the formulas of the nodes after it: the formula path
    to its data and its properties, keyed as the path expects.
    """

    service = node.service.specific
    service_type = service.get_type()
    schema = service_type.generate_schema(service) or {}
    if schema.get("type") == "array":
        schema = schema.get("items") or {}
    path = f"previous_node.{node.id}"
    if service_type.returns_list:
        path += ".0"
    return {"formula_path": path, "properties": _compact_properties(schema)}


def describe_node(
    node: AutomationNode,
    previous: AutomationNode | None = None,
    output: str = "",
) -> dict[str, Any]:
    """A node as the node tools return it."""

    description: dict[str, Any] = {
        "id": node.id,
        "label": node.label,
        "type": node.get_type().type,
    }
    if previous is not None:
        description["previous_node_ref"] = str(previous.id)
        if output:
            labels = {edge["uid"]: edge["label"] for edge in router_edges(previous)}
            description["router_edge_label"] = labels.get(output, "")
    edges = router_edges(node)
    if edges:
        description["edges"] = edges
    return description


def list_nodes(
    ctx: ToolContext,
    workflow_id: Annotated[
        int, Field(description="The ID of the workflow to list nodes for.")
    ],
) -> dict[str, Any]:
    """
    List the nodes of a workflow in execution order, the trigger first. Each node
    has its id, label and type, the node it follows (previous_node_ref) and, on a
    router branch, the branch label. A router lists its branches. output_schema
    says what a node outputs: a later node's formula reads a property with
    get('<formula_path>.<property key>').
    """

    workflow = get_workflow_in_workspace(ctx, workflow_id)
    return {
        "nodes": [
            {
                **describe_node(node, previous, output),
                "output_schema": output_schema(node),
            }
            for node, previous, output in nodes_in_order(ctx.user, workflow)
        ]
    }
