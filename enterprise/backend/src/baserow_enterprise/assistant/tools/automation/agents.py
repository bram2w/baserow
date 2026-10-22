"""
Sub-agents for the automation assistant tools.

Contains:
- ``AssistantFormulaContext``: Automation-specific formula context.
- ``get_generate_formulas_tool()``: Gets the automation formula generator.
- ``repair_formula_errors()``: Generates the formulas the shared tools could not
  store, after their transaction.
"""

from typing import TYPE_CHECKING, Any, Callable

from django.db import transaction
from django.utils.translation import gettext as _

from loguru import logger

from baserow.contrib.automation.nodes.models import AutomationNode
from baserow.contrib.automation.tools import nodes as shared_nodes
from baserow.contrib.automation.tools.formulas import formula_error
from baserow.core.tools import ToolContext
from baserow_enterprise.assistant.tools.shared import raise_if_permission_denied
from baserow_enterprise.assistant.tools.shared.agents import get_formula_generator
from baserow_enterprise.assistant.tools.shared.formula_utils import (
    FORMULA_PREFIX,
    BaseFormulaContext,
    create_example_from_json_schema,
    formula_desc,
    minimize_json_schema,
)

from .prompts import GENERATE_FORMULA_PROMPT
from .types.node import AutomationFieldValue, NodeUpdate, RouterEdgeUpdate

if TYPE_CHECKING:
    from baserow_enterprise.assistant.deps import ToolHelpers
    from baserow_enterprise.assistant.model_profiles import (
        ResolvedAssistantModelProfile,
    )


class AssistantFormulaContext(BaseFormulaContext):
    """
    Automation-specific formula context.

    Wraps node data in the ``{"previous_node": {...}}`` structure expected
    by automation formula ``get()`` paths.
    """

    def add_node_context(
        self,
        node_id: int | str,
        node_context: dict[str, Any],
        context_metadata: dict[str, dict[str, str]] | None = None,
    ):
        """Add a node's output values to the formula context."""
        self.add_context(str(node_id), node_context, context_metadata)

    def get_formula_context(self) -> dict[str, Any]:
        """Return context wrapped in ``previous_node`` for automation formulas."""
        return {"previous_node": self.context}

    def __getitem__(self, key) -> Any:
        """Resolve paths like ``previous_node.1.0.field_name``."""
        return self._resolve_path(key, "previous_node")


def get_generate_formulas_tool(
    model_profile: "ResolvedAssistantModelProfile",
) -> Callable[[dict, BaseFormulaContext, int], dict[str, str]]:
    """Get the automation formula generator using the request model profile.

    :param model_profile: The model profile resolved for the assistant request.
    :return: A callable that generates automation formulas.
    """

    return get_formula_generator(GENERATE_FORMULA_PROMPT, model_profile)


# What each value is, for the generator, by the field a formula error names.
_DESCRIPTIONS = {
    "to_emails": "A comma separated list of email addresses to send the email to.",
    "cc_emails": "A comma separated list of email addresses to CC the email to.",
    "bcc_emails": "A comma separated list of email addresses to BCC the email to.",
    "subject": "The subject of the email.",
    "body": "The body content of the email.",
    "text": "The message content.",
    "prompt": "The AI prompt.",
    "row_id": "The ID of the row to act on.",
    "condition": "A boolean condition for the router branch.",
}


def _request_key(error: dict[str, Any]) -> Any:
    """The key the generator answers a formula error under."""

    if "field_id" in error:
        return error["field_id"]
    if "edge_label" in error:
        return error["edge_label"]
    return error["field"]


def _describe(error: dict[str, Any], base: str) -> str:
    formula = error["formula"]
    description = f"{base} Value to resolve: {formula_desc(formula) if formula.strip() else 'not given'}"
    if formula.strip() and FORMULA_PREFIX not in formula.lower():
        description += f" It was written as an invalid formula: {error['error']}"
    return description


def formula_requests(
    node: AutomationNode, errors: list[dict[str, Any]]
) -> dict[Any, Any]:
    """
    What to ask the generator for a node's formula errors, keyed as
    ``_request_key``. A row value is described with its field.
    """

    fields = {}
    if any("field_id" in error for error in errors):
        service = node.service.specific
        schema = service.get_type().generate_schema(service) or {}
        fields = {
            int(field["id"]): field
            for field in minimize_json_schema(schema).values()
            if "id" in field
        }

    requests: dict[Any, Any] = {}
    for error in errors:
        key = _request_key(error)
        if "field_id" in error:
            field = fields.get(error["field_id"], {"desc": ""})
            requests[key] = {**field, "desc": _describe(error, field["desc"])}
        else:
            requests[key] = _describe(error, _DESCRIPTIONS.get(error["field"], ""))
    return requests


def _formula_update(
    node_id: int, errors: list[dict[str, Any]], generated: dict[Any, str]
) -> NodeUpdate:
    """The update that writes the generated formulas of a node's errors."""

    values: dict[str, Any] = {}
    for error in errors:
        formula = generated[_request_key(error)]
        if "field_id" in error:
            values.setdefault("values", []).append(
                AutomationFieldValue(field_id=error["field_id"], value=formula)
            )
        elif "edge_label" in error:
            values.setdefault("edges", []).append(
                RouterEdgeUpdate(label=error["edge_label"], condition=formula)
            )
        else:
            values[error["field"]] = formula
    return NodeUpdate(node_id=node_id, **values)


def workflow_formula_context(
    user, workflow, refs: dict[int, str] | None = None
) -> "AssistantFormulaContext":
    """
    The example data of every node of a workflow, for the generator.

    :param refs: The ref each node was created under, to help the generator.
    """

    context = AssistantFormulaContext()
    for node, previous, _output in shared_nodes.nodes_in_order(user, workflow):
        service = node.service.specific
        schema = service.get_type().generate_schema(service)
        if not schema:
            continue
        metadata = minimize_json_schema(schema)
        metadata["node_id"] = node.id
        metadata["label"] = node.label
        if refs and node.id in refs:
            metadata["node_ref"] = refs[node.id]
        if previous is not None:
            metadata["previous_node_id"] = previous.id
        context.add_node_context(
            node.id, create_example_from_json_schema(schema), metadata
        )
    return context


def repair_formula_errors(
    tool_context: ToolContext,
    tool_helpers: "ToolHelpers",
    formula_errors: list[dict[str, Any]],
    refs: dict[int, str] | None = None,
) -> list[dict[str, Any]]:
    """
    Generate the formulas the shared tools could not store, and write each node's
    in its own transaction. Runs after the nodes are committed, so the model is
    never called inside a transaction.

    :param refs: The ref each node was created under, to help the generator.
    :return: The formula errors that remain.
    """

    if not formula_errors:
        return []

    generate_formula = get_generate_formulas_tool(tool_helpers.model_profile)
    field_ids = shared_nodes.table_field_ids()
    remaining: list[dict[str, Any]] = []
    by_node: dict[int, list[dict[str, Any]]] = {}
    for error in formula_errors:
        by_node.setdefault(error["node_id"], []).append(error)
    for node_id, node_errors in by_node.items():
        node = shared_nodes.get_node_in_workspace(tool_context, node_id)
        tool_context.update_status(
            _("Generating formulas for node '%(label)s'...") % {"label": node.label}
        )
        try:
            context = workflow_formula_context(tool_context.user, node.workflow, refs)
            generated = generate_formula(formula_requests(node, node_errors), context)
        except Exception as exc:
            raise_if_permission_denied(exc)
            logger.exception(
                "Failed to generate formulas for node {}: {}", node_id, exc
            )
            remaining.extend({**error, "error": str(exc)} for error in node_errors)
            continue

        generated = generated or {}
        repaired = [e for e in node_errors if _request_key(e) in generated]
        remaining.extend(e for e in node_errors if _request_key(e) not in generated)
        if not repaired:
            continue
        with transaction.atomic():
            node, values = shared_nodes.update_node(
                tool_context,
                node.workflow,
                _formula_update(node_id, repaired, generated),
                field_ids,
                as_formulas=True,
            )
        remaining.extend(
            formula_error(node, exc, **target) for exc, target in values.invalid
        )
    return remaining
