import json

import pytest
from asgiref.sync import async_to_sync

from baserow.core.exceptions import InstanceTypeAlreadyRegistered
from baserow.core.mcp.exceptions import MCPToolInputError
from baserow.core.mcp.registries import mcp_tool_registry
from baserow_enterprise.assistant.mcp.tools import (
    AssistantMCPTool,
    build_mcp_deps,
    register_assistant_mcp_tools,
)

PHASE_ONE_TOOLS = {
    "list_views": ("database_read", "List views"),
    "list_pages": ("builder_read", "List pages"),
    "list_data_sources": ("builder_read", "List data sources"),
    "list_elements": ("builder_read", "List elements"),
    "list_actions": ("builder_read", "List page actions"),
    "list_workflows": ("automation_read", "List workflows"),
    "list_nodes": ("automation_read", "List workflow nodes"),
}


@pytest.mark.parametrize("name,expected", PHASE_ONE_TOOLS.items())
def test_phase_one_tools_are_registered(name, expected):
    tool = mcp_tool_registry.get(name)
    assert isinstance(tool, AssistantMCPTool)
    assert (tool.group, tool.title) == expected
    assert tool.read_only is True
    assert tool.destructive is False


def test_only_phase_one_tools_are_registered():
    names = {
        t.type for t in mcp_tool_registry.get_all() if isinstance(t, AssistantMCPTool)
    }
    assert names == set(PHASE_ONE_TOOLS)


def test_register_twice_fails():
    with pytest.raises(InstanceTypeAlreadyRegistered):
        register_assistant_mcp_tools()


def test_kuma_only_tools_are_not_registered():
    names = {t.type for t in mcp_tool_registry.get_all()}
    for name in [
        "switch_mode",
        "ask_user",
        "navigate",
        "load_row_tools",
        "generate_formula",
    ]:
        assert name not in names


@pytest.mark.django_db
def test_bridge_lists_schema_without_thought(data_fixture):
    tool = mcp_tool_registry.get("list_views")
    endpoint = data_fixture.create_mcp_endpoint()
    [definition] = async_to_sync(tool.list)(endpoint)
    assert definition.name == "list_views"
    assert "thought" not in definition.inputSchema.get("properties", {})
    assert "thought" not in definition.inputSchema.get("required", [])
    assert "table_id" in definition.inputSchema["properties"]
    assert definition.annotations.readOnlyHint is True
    assert definition.annotations.destructiveHint is False
    assert definition.annotations.openWorldHint is False
    assert definition.annotations.title == "List views"
    assert "\n" not in definition.description


@pytest.mark.django_db
def test_bridge_does_not_mutate_kuma_schema(data_fixture):
    tool = mcp_tool_registry.get("list_views")
    endpoint = data_fixture.create_mcp_endpoint()
    async_to_sync(tool.list)(endpoint)
    schema = tool._tool.tool_def.parameters_json_schema
    assert "thought" in schema["properties"]
    assert "thought" in schema["required"]


@pytest.mark.django_db(transaction=True)
def test_bridge_calls_kuma_function(data_fixture):
    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=user)
    database = data_fixture.create_database_application(workspace=workspace)
    table = data_fixture.create_database_table(database=database)
    data_fixture.create_grid_view(table=table, name="All")
    endpoint = data_fixture.create_mcp_endpoint(user=user, workspace=workspace)
    [content] = async_to_sync(mcp_tool_registry.get("list_views").call)(
        endpoint, {"table_id": table.id}
    )
    assert "All" in content.text
    assert json.loads(content.text)["views"][0]["name"] == "All"


@pytest.mark.django_db(transaction=True)
def test_bridge_missing_object_is_an_input_error(data_fixture):
    endpoint = data_fixture.create_mcp_endpoint()
    with pytest.raises(MCPToolInputError):
        async_to_sync(mcp_tool_registry.get("list_views").call)(
            endpoint, {"table_id": 999999}
        )


@pytest.mark.django_db(transaction=True)
def test_bridge_awaits_async_functions(data_fixture):
    endpoint = data_fixture.create_mcp_endpoint()
    tool = mcp_tool_registry.get("list_views")

    class FakeSchema:
        is_async = True

        class validator:
            @staticmethod
            def validate_python(args):
                return {}

    class FakeTool:
        function_schema = FakeSchema

        @staticmethod
        async def function(ctx):
            return {"deps": ctx.deps.workspace.id}

    original = tool._tool
    tool._tool = FakeTool
    try:
        [content] = async_to_sync(tool.call)(endpoint, {})
    finally:
        tool._tool = original
    assert json.loads(content.text) == {"deps": endpoint.workspace_id}


@pytest.mark.django_db
def test_build_mcp_deps_uses_endpoint_scope(data_fixture):
    endpoint = data_fixture.create_mcp_endpoint()
    deps = build_mcp_deps(endpoint)
    assert deps.user == endpoint.user
    assert deps.workspace == endpoint.workspace
    deps.tool_helpers.update_status("x")


@pytest.mark.django_db
def test_bridge_tool_unavailable_when_tool_type_cannot_be_used(
    data_fixture, monkeypatch
):
    endpoint = data_fixture.create_mcp_endpoint()
    tool = mcp_tool_registry.get("list_views")
    assert tool.is_available(endpoint) is True
    monkeypatch.setattr(tool._tool_type, "can_use", lambda user, workspace: False)
    assert tool.is_available(endpoint) is False
    assert "list_views" not in [
        t.name for t in mcp_tool_registry.get_allowed_tools(endpoint)
    ]
    assert mcp_tool_registry.get_allowed_tool(endpoint, "list_views") is None


@pytest.mark.django_db
def test_endpoint_without_allow_list_cannot_use_kuma_tools(data_fixture):
    from asgiref.sync import async_to_sync as a2s
    from mcp.shared.memory import (
        create_connected_server_and_client_session as client_session,
    )

    from baserow.core.mcp import BaserowMCPServer, current_key
    from baserow.core.mcp.constants import LEGACY_DEFAULT_TOOLS

    endpoint = data_fixture.create_mcp_endpoint(allowed_tools=None)
    token = current_key.set(endpoint.key)

    async def inner():
        async with client_session(BaserowMCPServer()._mcp_server) as client:
            names = {t.name for t in (await client.list_tools()).tools}
            assert names == set(LEGACY_DEFAULT_TOOLS)
            assert not names & set(PHASE_ONE_TOOLS)
            result = await client.call_tool("list_pages", {"application_id": 1})
            assert result.isError is True
            assert result.content[0].text == "Tool 'list_pages' not found."

    try:
        from django.db import transaction

        with transaction.atomic():
            a2s(inner)()
    finally:
        current_key.reset(token)
