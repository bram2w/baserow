import re
from typing import TYPE_CHECKING

from asgiref.sync import sync_to_async
from pydantic_ai import RunContext, Tool
from pydantic_ai.toolsets import FunctionToolset

from baserow.core.services.exceptions import (
    ServiceImproperlyConfiguredDispatchException,
)
from baserow.core.services.handler import ServiceHandler

from ..agent_dispatch_context import AgentDispatchContext
from .registries import AgentToolType

if TYPE_CHECKING:
    from ..deps import AgentRunDeps
    from ..models import AgentTool

_INPUT_TYPE_TO_JSON_SCHEMA = {
    "string": {"type": "string"},
    "number": {"type": "number"},
    "boolean": {"type": "boolean"},
}


def _slugify_tool_name(name: str) -> str:
    return re.sub(r"[^a-z0-9_]+", "_", (name or "").lower()).strip("_")


def get_service_tool_name(tool: "AgentTool") -> str:
    """
    The runtime name of a service tool. Two tools named alike ("Send email"
    for Gmail and for Outlook) would clash and break every run, so the later
    one carries its id.
    """

    slug = _slugify_tool_name(tool.name) or f"service_tool_{tool.id}"
    if tool.agent_id is None or tool.id is None:
        return slug
    earlier_names = tool.agent.tools.filter(
        id__lt=tool.id, service__isnull=False
    ).values_list("name", flat=True)
    if any(_slugify_tool_name(name) == slug for name in earlier_names):
        return f"{slug}_{tool.id}"
    return slug


def build_service_tool_schema(tool: "AgentTool") -> dict:
    """
    Builds the JSON schema for the tool's arguments from the user-declared
    runtime inputs. The user configures the service itself; the model only
    supplies these inputs, referenced in service formulas as
    `get('tool_input.<name>')`.
    """

    properties = {}
    required = []

    for input_definition in tool.config.get("inputs", []):
        name = input_definition.get("name")
        if not name:
            continue
        schema = dict(
            _INPUT_TYPE_TO_JSON_SCHEMA.get(
                input_definition.get("type", "string"),
                _INPUT_TYPE_TO_JSON_SCHEMA["string"],
            )
        )
        if input_definition.get("description"):
            schema["description"] = input_definition["description"]
        properties[name] = schema
        if input_definition.get("required", True):
            required.append(name)

    return {
        "type": "object",
        "properties": properties,
        "required": required,
        "additionalProperties": False,
    }


def build_service_tool(tool: "AgentTool", deps: "AgentRunDeps") -> Tool:
    service = tool.service.specific
    service_type = service.get_type()
    description = (
        tool.config.get("description")
        or f"Executes the configured {service_type.type} action."
    )

    # Resolved here, outside the async tool call, so no database access
    # happens from the event loop.
    identity = tool.identity
    if identity is None and acts_as_user(tool, deps):
        identity = getattr(deps, "initiating_user", None)

    async def run_service_tool(ctx: RunContext["AgentRunDeps"], **kwargs):
        ctx.deps.tool_helpers.raise_if_cancelled()
        dispatch_context = AgentDispatchContext(
            chat=ctx.deps.chat,
            runtime_inputs=kwargs,
            # A tool with its own identity acts as that workspace agent even
            # though the service's integration names the application's.
            actor=identity or ctx.deps.user,
            actor_overrides_integration=identity is not None,
        )

        def dispatch():
            from ..actions import DispatchAgentToolActionType

            result = ServiceHandler().dispatch_service(service, dispatch_context)
            # Audited as whoever the tool acted as, like the row actions the
            # local Baserow services already register themselves.
            DispatchAgentToolActionType.do(
                dispatch_context.actor, tool, service_type.type, ctx.deps.chat
            )
            return result

        try:
            result = await sync_to_async(dispatch)()
        except ServiceImproperlyConfiguredDispatchException as exc:
            return {"error": f"The tool's service is misconfigured: {exc}"}
        except Exception as exc:
            return {"error": f"The tool failed: {exc}"}

        return result.data

    return Tool.from_schema(
        run_service_tool,
        name=get_service_tool_name(tool),
        description=description,
        json_schema=build_service_tool_schema(tool),
        takes_ctx=True,
    )


def acts_as_user(tool: "AgentTool", deps: "AgentRunDeps") -> bool:
    """
    Whether the tool acts on behalf of the conversation's user: by its own
    setting, or by the application's when the tool has no identity of its own.
    """

    if tool.identity_id is not None:
        return False
    return tool.act_as_user or tool.agent.application.act_as_user


def needs_user(tool: "AgentTool", deps: "AgentRunDeps", service_type) -> bool:
    """
    Whether the tool can't run in a conversation without a Baserow user. A
    tool set to act as the user never runs without one. Inheriting that from
    the application only matters for services whose effect depends on who
    acts: workspace services would fall back to the integration's user and
    "Run agent" would start the other agent as the system, while an email or
    a web request doesn't depend on who acts.
    """

    from baserow.contrib.integrations.local_baserow.service_types import (
        LocalBaserowServiceType,
    )
    from baserow_enterprise.integrations.core.service_types import (
        CoreRunAgentServiceType,
    )

    if not acts_as_user(tool, deps):
        return False
    return tool.act_as_user or isinstance(
        service_type, (LocalBaserowServiceType, CoreRunAgentServiceType)
    )


class ServiceAgentToolType(AgentToolType):
    """
    Exposes a user-configured action service (send Slack message, send email,
    HTTP request, create rows, start workflow, ...) as a callable tool.
    """

    type = "service"
    is_configurable = True

    def owns_tool_name(self, tool: "AgentTool", tool_name: str) -> bool:
        return get_service_tool_name(tool) == tool_name

    def apply_dont_ask_again(self, tool: "AgentTool", tool_name: str) -> dict:
        return {**tool.config, "require_approval": False}

    def build_toolsets(self, tool: "AgentTool", deps: "AgentRunDeps") -> list:
        from .gating import wrap_approval_required

        if tool.service_id is None:
            return []
        if getattr(deps, "initiating_user", None) is None and needs_user(
            tool, deps, tool.service.specific.get_type()
        ):
            deps.system_notes.append(
                f"The tool '{get_service_tool_name(tool)}' acts on behalf of the "
                "Baserow user of the conversation and is unavailable because "
                "this conversation has none."
            )
            return []

        toolset = FunctionToolset([build_service_tool(tool, deps)], max_retries=3)
        # Action services always change something (rows, emails, requests),
        # so they sit behind the approval queue unless explicitly disabled.
        if tool.config.get("require_approval", True):
            return [wrap_approval_required(toolset)]
        return [toolset]
