from unittest.mock import patch

import pytest
from asgiref.sync import async_to_sync
from mcp.shared.memory import (
    create_connected_server_and_client_session as client_session,
)

from baserow.core.mcp import BaserowMCPServer, current_key
from baserow.core.mcp.registries import MCPTool, MCPToolRegistry


class AvailableTool(MCPTool):
    """An available tool."""

    type = "availability_available"


class UnavailableTool(MCPTool):
    """An unavailable tool."""

    type = "availability_unavailable"

    def is_available(self, endpoint):
        return False


def _registry():
    registry = MCPToolRegistry()
    registry.register(AvailableTool())
    registry.register(UnavailableTool())
    return registry


def test_tool_defaults():
    assert AvailableTool().is_available(None) is True
    assert AvailableTool().group is None


@pytest.mark.django_db
def test_unavailable_tool_is_not_allowed(data_fixture):
    endpoint = data_fixture.create_mcp_endpoint()
    registry = _registry()

    assert [t.name for t in registry.get_allowed_tools(endpoint)] == [
        "availability_available"
    ]
    assert registry.get_allowed_tool(endpoint, "availability_unavailable") is None
    assert registry.get_allowed_tool(endpoint, "availability_available") is not None


@pytest.mark.django_db
def test_unavailable_tool_neither_lists_nor_calls_over_server(data_fixture):
    endpoint = data_fixture.create_mcp_endpoint(allowed_tools=None)
    registry = _registry()

    async def inner():
        server = BaserowMCPServer()
        token = current_key.set(endpoint.key)
        try:
            async with client_session(server._mcp_server) as client:
                listed = await client.list_tools()
                assert [t.name for t in listed.tools] == ["availability_available"]
                result = await client.call_tool("availability_unavailable", {})
                assert result.isError is True
                assert "not found" in result.content[0].text
        finally:
            current_key.reset(token)

    with patch("baserow.core.mcp.registries.mcp_tool_registry", registry):
        async_to_sync(inner)()
