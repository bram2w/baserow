import copy
import json
from typing import Any

from asgiref.sync import async_to_sync, sync_to_async
from pydantic import ValidationError
from pydantic_ai import ModelRetry

from baserow.core.mcp.exceptions import MCPToolInputError, format_validation_error
from baserow.core.mcp.models import MCPEndpoint
from baserow.core.mcp.registries import MCPTool, mcp_tool_registry
from baserow_enterprise.assistant.deps import AssistantDeps, ToolHelpers
from baserow_enterprise.assistant.tools.mcp_meta import MCPToolMeta, get_mcp_meta
from baserow_enterprise.assistant.tools.registries import assistant_tool_registry
from baserow_enterprise.assistant.tools.shared.errors import ToolInputError


def build_mcp_deps(endpoint: MCPEndpoint) -> AssistantDeps:
    """Deps for a Kuma tool call made through the endpoint, without a chat."""

    return AssistantDeps(
        user=endpoint.user,
        workspace=endpoint.workspace,
        tool_helpers=ToolHelpers(
            update_status=lambda _: None,
            navigate_to=lambda _: "",
            model_profile=None,
        ),
    )


class _Ctx:
    """The part of ``RunContext`` that the MCP-exposed Kuma tools read."""

    def __init__(self, deps: AssistantDeps):
        self.deps = deps


def _strip_thought(schema: dict) -> dict:
    schema = copy.deepcopy(schema)
    schema.get("properties", {}).pop("thought", None)
    if "required" in schema:
        schema["required"] = [r for r in schema["required"] if r != "thought"]
    return schema


class AssistantMCPTool(MCPTool):
    """Offers a Kuma tool function over MCP, using the same definition."""

    def __init__(self, tool, tool_type, meta: MCPToolMeta):
        self.type = tool.name
        self.title = meta.title
        self.read_only = meta.read_only
        self.destructive = meta.destructive
        self.group = meta.group
        self._tool = tool
        self._tool_type = tool_type
        super().__init__()

    def is_available(self, endpoint: MCPEndpoint) -> bool:
        return self._tool_type.can_use(endpoint.user, endpoint.workspace)

    async def list(self, endpoint: MCPEndpoint):
        from mcp import Tool
        from mcp.types import ToolAnnotations

        return [
            Tool(
                name=self.type,
                description=" ".join((self._tool.description or "").split()),
                inputSchema=_strip_thought(self._tool.tool_def.parameters_json_schema),
                annotations=ToolAnnotations(
                    title=self.title,
                    readOnlyHint=self.read_only,
                    destructiveHint=self.destructive,
                    openWorldHint=False,
                ),
            )
        ]

    async def call(self, endpoint: MCPEndpoint, call_arguments: dict[str, Any]):
        from mcp.types import TextContent

        result = await sync_to_async(self._sync_call)(endpoint, call_arguments)
        text = result if isinstance(result, str) else json.dumps(result, default=str)
        return [TextContent(type="text", text=text)]

    def _sync_call(self, endpoint: MCPEndpoint, args: dict[str, Any]) -> Any:
        schema = self._tool.function_schema
        try:
            kwargs = schema.validator.validate_python({**args, "thought": ""})
        except ValidationError as exc:
            raise MCPToolInputError(format_validation_error(exc)) from exc
        ctx = _Ctx(build_mcp_deps(endpoint))
        try:
            if schema.is_async:
                return async_to_sync(self._tool.function)(ctx, **kwargs)
            return self._tool.function(ctx, **kwargs)
        except (ModelRetry, ToolInputError) as exc:
            raise MCPToolInputError(str(exc)) from exc


def register_assistant_mcp_tools() -> list[str]:
    """
    Register an MCP tool for every Kuma tool function marked with ``mcp_tool``.

    :return: The names of the registered tools.
    """

    names = []
    for tool_type in assistant_tool_registry.get_all():
        toolset = tool_type.get_toolset()
        for fn in tool_type.get_tool_functions():
            meta = get_mcp_meta(fn)
            if meta is None:
                continue
            tool = toolset.tools[fn.__name__]
            mcp_tool_registry.register(AssistantMCPTool(tool, tool_type, meta))
            names.append(tool.name)
    return names
