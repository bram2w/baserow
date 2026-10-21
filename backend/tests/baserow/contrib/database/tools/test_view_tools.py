"""Tests for the view tools shared by MCP and Kuma."""

import json

from django.db import transaction

import pytest
from asgiref.sync import async_to_sync
from mcp.shared.memory import (
    create_connected_server_and_client_session as client_session,
)

from baserow.contrib.database.tools.views import (
    ViewFilterItemCreate,
    ViewFiltersArgs,
    ViewItemCreate,
    create_view_filters,
    create_views,
)
from baserow.contrib.database.views.models import View, ViewFilter
from baserow.core.mcp import BaserowMCPServer, current_key
from baserow.core.tools import ToolContext

VIEW_TOOLS = ["create_views", "create_view_filters"]


@pytest.fixture
def table_ctx(data_fixture):
    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=user)
    database = data_fixture.create_database_application(workspace=workspace)
    table = data_fixture.create_database_table(database=database)
    data_fixture.create_text_field(table=table, name="Name", primary=True)
    return ToolContext(user=user, workspace=workspace), table


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
def test_create_views_skips_names_already_used(data_fixture, table_ctx):
    ctx, table = table_ctx
    data_fixture.create_grid_view(table=table, name="Grid")

    result = create_views(
        ctx,
        table.id,
        [
            ViewItemCreate(name="Grid", type="grid"),
            ViewItemCreate(name="Open", type="grid"),
            ViewItemCreate(name="Open", type="grid"),
        ],
    )

    assert [view["name"] for view in result["created_views"]] == ["Open"]
    assert result["skipped_views"] == ["Grid", "Open"]
    assert sorted(View.objects.filter(table=table).values_list("name", flat=True)) == [
        "Grid",
        "Open",
    ]


@pytest.mark.django_db
def test_create_views_without_duplicates_lists_no_skipped_views(table_ctx):
    ctx, table = table_ctx

    result = create_views(ctx, table.id, [ViewItemCreate(name="All", type="grid")])

    assert "skipped_views" not in result


@pytest.mark.django_db
def test_create_view_filters_returns_the_skipped_filters(data_fixture, table_ctx):
    ctx, table = table_ctx
    number = data_fixture.create_number_field(table=table, name="Amount")
    view = data_fixture.create_grid_view(table=table)

    result = create_view_filters(
        ctx,
        [
            ViewFiltersArgs(
                view_id=view.id,
                filters=[
                    ViewFilterItemCreate(
                        field_id=number.id,
                        type="number",
                        operator="higher_than",
                        value=10,
                    ),
                    ViewFilterItemCreate(
                        field_id=number.id, type="text", operator="equal", value="x"
                    ),
                ],
            )
        ],
    )

    (entry,) = result["created_view_filters"]
    assert [f["field_id"] for f in entry["filters"]] == [number.id]
    (skipped,) = entry["skipped_filters"]
    assert skipped["field_id"] == number.id
    assert skipped["type"] == "text"
    assert "is type 'number'" in skipped["error"]
    assert result["changed"] is True
    assert ViewFilter.objects.filter(view=view).count() == 1


@pytest.mark.django_db
def test_view_tools_over_mcp(data_fixture):
    endpoint = data_fixture.create_mcp_endpoint(allowed_tools=VIEW_TOOLS)
    database = data_fixture.create_database_application(workspace=endpoint.workspace)
    table = data_fixture.create_database_table(database=database)
    name = data_fixture.create_text_field(table=table, name="Name", primary=True)

    async def callback(client):
        listed = await client.list_tools()
        created = await client.call_tool(
            "create_views",
            {"table_id": table.id, "views": [{"name": "Open", "type": "grid"}]},
        )
        view_id = json.loads(created.content[0].text)["created_views"][0]["id"]
        filtered = await client.call_tool(
            "create_view_filters",
            {
                "view_filters": [
                    {
                        "view_id": view_id,
                        "filters": [
                            {
                                "field_id": name.id,
                                "type": "text",
                                "operator": "contains",
                                "value": "a",
                            }
                        ],
                    }
                ]
            },
        )
        return listed, view_id, filtered

    listed, view_id, filtered = _session(endpoint, callback)

    tools = {tool.name: tool for tool in listed.tools}
    assert set(tools["create_views"].inputSchema["properties"]) == {
        "table_id",
        "views",
    }
    assert set(tools["create_view_filters"].inputSchema["properties"]) == {
        "view_filters"
    }
    for tool in (tools["create_views"], tools["create_view_filters"]):
        for kuma_only in ("ask_user", "navigate", "get_tables_schema", "sample"):
            assert kuma_only not in tool.description
    assert filtered.isError is False
    assert ViewFilter.objects.get(view_id=view_id).type == "contains"


@pytest.mark.django_db
def test_create_views_over_mcp_table_in_other_workspace_is_not_found(data_fixture):
    endpoint = data_fixture.create_mcp_endpoint(allowed_tools=VIEW_TOOLS)
    other_table = data_fixture.create_database_table(user=endpoint.user)

    result = _call(
        endpoint,
        "create_views",
        {"table_id": other_table.id, "views": [{"name": "Open", "type": "grid"}]},
    )

    assert result.isError is True
    assert result.content[0].text == "Not found in this workspace."
    assert not View.objects.filter(table=other_table).exists()


@pytest.mark.django_db
def test_create_view_filters_over_mcp_view_in_other_workspace_is_not_found(
    data_fixture,
):
    endpoint = data_fixture.create_mcp_endpoint(allowed_tools=VIEW_TOOLS)
    other_table = data_fixture.create_database_table(user=endpoint.user)
    field = data_fixture.create_text_field(table=other_table, name="Name")
    other_view = data_fixture.create_grid_view(table=other_table)

    result = _call(
        endpoint,
        "create_view_filters",
        {
            "view_filters": [
                {
                    "view_id": other_view.id,
                    "filters": [
                        {
                            "field_id": field.id,
                            "type": "text",
                            "operator": "equal",
                            "value": "a",
                        }
                    ],
                }
            ]
        },
    )

    assert result.isError is True
    assert result.content[0].text == "Not found in this workspace."
    assert not ViewFilter.objects.filter(view=other_view).exists()
