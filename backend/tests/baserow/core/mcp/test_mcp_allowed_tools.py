import pytest

from baserow.core.mcp.constants import LEGACY_DEFAULT_TOOLS
from baserow.core.mcp.registries import MCPTool, MCPToolRegistry


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
