"""
A read tool offered over MCP must never return an object that lives in another
workspace, even when the endpoint's user can access that workspace too.
"""

import pytest
from asgiref.sync import async_to_sync

from baserow.core.exceptions import ApplicationDoesNotExist
from baserow.core.mcp.exceptions import MCPToolInputError
from baserow.core.mcp.registries import mcp_tool_registry


def _call(endpoint, name, arguments):
    return async_to_sync(mcp_tool_registry.get(name).call)(endpoint, arguments)


@pytest.fixture
def two_workspaces(data_fixture):
    user = data_fixture.create_user()
    mine = data_fixture.create_workspace(user=user)
    other = data_fixture.create_workspace(user=user)
    endpoint = data_fixture.create_mcp_endpoint(user=user, workspace=mine)
    return user, mine, other, endpoint


@pytest.mark.django_db(transaction=True)
def test_list_views_other_workspace(data_fixture, two_workspaces):
    user, mine, other, endpoint = two_workspaces
    database = data_fixture.create_database_application(workspace=other)
    table = data_fixture.create_database_table(database=database)
    data_fixture.create_grid_view(table=table, name="Secret")
    with pytest.raises(MCPToolInputError) as exc:
        _call(endpoint, "list_views", {"table_id": table.id})
    assert "not found" in str(exc.value)
    assert "Secret" not in str(exc.value)


@pytest.mark.django_db(transaction=True)
def test_list_pages_other_workspace(data_fixture, two_workspaces):
    user, mine, other, endpoint = two_workspaces
    builder = data_fixture.create_builder_application(user=user, workspace=other)
    data_fixture.create_builder_page(builder=builder, name="Secret")
    with pytest.raises(MCPToolInputError) as exc:
        _call(endpoint, "list_pages", {"application_id": builder.id})
    assert "not found in this workspace" in str(exc.value)
    assert "Secret" not in str(exc.value)


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("name", ["list_data_sources", "list_elements", "list_actions"])
def test_page_tools_other_workspace(data_fixture, two_workspaces, name):
    user, mine, other, endpoint = two_workspaces
    builder = data_fixture.create_builder_application(user=user, workspace=other)
    page = data_fixture.create_builder_page(builder=builder, name="Secret")
    data_fixture.create_builder_heading_element(page=page, value="'Secret'")
    with pytest.raises(MCPToolInputError) as exc:
        _call(endpoint, name, {"page_id": page.id})
    assert "not found" in str(exc.value)
    assert "Secret" not in str(exc.value)


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("name", ["list_data_sources", "list_elements", "list_actions"])
def test_page_tools_same_workspace_work(data_fixture, two_workspaces, name):
    user, mine, other, endpoint = two_workspaces
    builder = data_fixture.create_builder_application(user=user, workspace=mine)
    page = data_fixture.create_builder_page(builder=builder)
    [content] = _call(endpoint, name, {"page_id": page.id})
    assert content.text


@pytest.mark.django_db(transaction=True)
def test_list_workflows_other_workspace(data_fixture, two_workspaces):
    user, mine, other, endpoint = two_workspaces
    automation = data_fixture.create_automation_application(user=user, workspace=other)
    data_fixture.create_automation_workflow(automation=automation, name="Secret")
    with pytest.raises(ApplicationDoesNotExist) as exc:
        _call(endpoint, "list_workflows", {"automation_id": automation.id})
    assert "does not exist" in str(exc.value)
    assert "Secret" not in str(exc.value)


@pytest.mark.django_db(transaction=True)
def test_list_nodes_other_workspace(data_fixture, two_workspaces):
    user, mine, other, endpoint = two_workspaces
    automation = data_fixture.create_automation_application(user=user, workspace=other)
    workflow = data_fixture.create_automation_workflow(automation=automation)
    with pytest.raises(ValueError) as exc:
        _call(endpoint, "list_nodes", {"workflow_id": workflow.id})
    assert "Workflow not in workspace" in str(exc.value)
