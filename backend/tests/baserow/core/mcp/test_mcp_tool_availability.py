from unittest.mock import patch

import pytest
from asgiref.sync import async_to_sync
from mcp.shared.memory import (
    create_connected_server_and_client_session as client_session,
)

from baserow.core.mcp import BaserowMCPServer, current_key
from baserow.core.mcp.constants import LEGACY_DEFAULT_TOOLS
from baserow.core.mcp.registries import MCPTool, MCPToolRegistry


class AvailableTool(MCPTool):
    """An available tool."""

    type = "availability_available"


class UnavailableTool(MCPTool):
    """An unavailable tool."""

    type = "availability_unavailable"

    def is_available(self, endpoint):
        return False


NAMES = ["availability_available", "availability_unavailable"]


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
    endpoint = data_fixture.create_mcp_endpoint(allowed_tools=NAMES)
    registry = _registry()

    assert [t.name for t in registry.get_allowed_tools(endpoint)] == [
        "availability_available"
    ]
    assert registry.get_allowed_tool(endpoint, "availability_unavailable") is None
    assert registry.get_allowed_tool(endpoint, "availability_available") is not None


@pytest.mark.django_db
def test_unavailable_tool_neither_lists_nor_calls_over_server(data_fixture):
    endpoint = data_fixture.create_mcp_endpoint(allowed_tools=NAMES)
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


@pytest.mark.django_db
def test_endpoint_without_allow_list_gets_only_legacy_default_tools(data_fixture):
    class Legacy(MCPTool):
        """Legacy."""

        type = LEGACY_DEFAULT_TOOLS[0]

    class New(MCPTool):
        """New."""

        type = "brand_new_tool"

    registry = MCPToolRegistry()
    registry.register(Legacy())
    registry.register(New())
    endpoint = data_fixture.create_mcp_endpoint(allowed_tools=None)

    assert [t.name for t in registry.get_allowed_tools(endpoint)] == [
        LEGACY_DEFAULT_TOOLS[0]
    ]
    assert registry.get_allowed_tool(endpoint, "brand_new_tool") is None
    assert registry.get_allowed_tool(endpoint, LEGACY_DEFAULT_TOOLS[0]) is not None


@pytest.mark.django_db
def test_failing_availability_check_hides_the_tool(data_fixture):
    class FailingTool(MCPTool):
        """A tool whose check fails."""

        type = "availability_failing"

        def is_available(self, endpoint):
            raise RuntimeError("secret internals")

    registry = MCPToolRegistry()
    registry.register(FailingTool())
    endpoint = data_fixture.create_mcp_endpoint(allowed_tools=["availability_failing"])

    assert registry.get_allowed_tools(endpoint) == []
    assert registry.get_allowed_tool(endpoint, "availability_failing") is None
