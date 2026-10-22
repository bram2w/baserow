"""The automation tools over MCP."""

import json

from django.db import transaction

import pytest
from asgiref.sync import async_to_sync
from mcp.shared.memory import (
    create_connected_server_and_client_session as client_session,
)

from baserow.core.mcp import BaserowMCPServer, current_key
from tests.baserow.contrib.automation.tools.conftest import create_workflow

READ_TOOLS = ["list_workflows", "list_nodes"]
KUMA_ONLY = ("ask_user", "navigate", "thought", "iterator", "load_")


def _session(endpoint, callback):
    async def inner():
        token = current_key.set(endpoint.key)
        try:
            async with client_session(BaserowMCPServer()._mcp_server) as client:
                return await callback(client)
        finally:
            current_key.reset(token)

    with transaction.atomic():
        return async_to_sync(inner)()


def _call(endpoint, name, arguments):
    async def callback(client):
        return await client.call_tool(name, arguments)

    return _session(endpoint, callback)


@pytest.mark.django_db
def test_read_tools_over_mcp(data_fixture):
    endpoint = data_fixture.create_mcp_endpoint(allowed_tools=READ_TOOLS)
    automation = data_fixture.create_automation_application(
        workspace=endpoint.workspace
    )
    workflow, trigger = create_workflow(endpoint.user, automation, "Flow")

    async def callback(client):
        listed = await client.list_tools()
        workflows = await client.call_tool("list_workflows", {})
        nodes = await client.call_tool("list_nodes", {"workflow_id": workflow.id})
        return listed, workflows, nodes

    listed, workflows, nodes = _session(endpoint, callback)

    tools = {tool.name: tool for tool in listed.tools}
    assert set(tools) == set(READ_TOOLS)
    for tool in tools.values():
        assert tool.annotations.readOnlyHint is True
        for kuma_only in KUMA_ONLY:
            assert kuma_only not in tool.description
    assert json.loads(workflows.content[0].text)["automations"][0]["workflows"] == [
        {"id": workflow.id, "name": "Flow", "state": "draft"}
    ]
    assert [node["id"] for node in json.loads(nodes.content[0].text)["nodes"]] == [
        trigger.id
    ]


@pytest.mark.django_db
def test_read_tools_over_mcp_hide_other_workspaces(data_fixture):
    endpoint = data_fixture.create_mcp_endpoint(allowed_tools=READ_TOOLS)
    elsewhere = data_fixture.create_automation_application(
        workspace=data_fixture.create_workspace(user=endpoint.user)
    )
    workflow, _ = create_workflow(endpoint.user, elsewhere)

    for name, arguments in (
        ("list_workflows", {"automation_id": elsewhere.id}),
        ("list_nodes", {"workflow_id": workflow.id}),
    ):
        result = _call(endpoint, name, arguments)
        assert result.isError is True
        assert result.content[0].text == "Not found in this workspace."


@pytest.mark.django_db
def test_read_tools_over_mcp_reject_unknown_arguments(data_fixture):
    endpoint = data_fixture.create_mcp_endpoint(allowed_tools=READ_TOOLS)

    result = _call(endpoint, "list_workflows", {"thought": "why"})

    assert result.isError is True
    assert "thought" in result.content[0].text
