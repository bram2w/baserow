"""Tests for the table read tools shared by MCP and Kuma."""

import json

from django.db import transaction

import pytest
from asgiref.sync import async_to_sync
from mcp.shared.memory import (
    create_connected_server_and_client_session as client_session,
)

from baserow.contrib.database.tools.tables import list_tables
from baserow.core.mcp import BaserowMCPServer, current_key
from baserow.core.tools import ToolContext


def _call(endpoint, name, arguments):
    async def inner():
        token = current_key.set(endpoint.key)
        try:
            async with client_session(BaserowMCPServer()._mcp_server) as client:
                return await client.call_tool(name, arguments)
        finally:
            current_key.reset(token)

    with transaction.atomic():
        return async_to_sync(inner)()


@pytest.fixture
def two_databases(data_fixture):
    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=user)
    sales = data_fixture.create_database_application(workspace=workspace, name="Sales")
    hr = data_fixture.create_database_application(workspace=workspace, name="HR")
    orders = data_fixture.create_database_table(database=sales, name="Orders")
    customers = data_fixture.create_database_table(database=sales, name="Customers")
    staff = data_fixture.create_database_table(database=hr, name="Staff")
    # Another workspace of the same user must stay hidden.
    data_fixture.create_database_table(user=user, name="Elsewhere")
    return ToolContext(user=user, workspace=workspace), orders, customers, staff


@pytest.mark.django_db
def test_list_tables_lists_the_workspace_tables(two_databases):
    ctx, orders, customers, staff = two_databases

    result = list_tables(ctx)

    assert result == [
        {
            "id": table.id,
            "name": table.name,
            "order": table.order,
            "database_id": table.database_id,
            "database_name": table.database.name,
        }
        for table in (orders, customers, staff)
    ]


@pytest.mark.django_db
@pytest.mark.parametrize(
    "filters,expected",
    [
        ({"database_name": "sal"}, ["Orders", "Customers"]),
        ({"table_names": ["cust", "staff"]}, ["Customers", "Staff"]),
        ({"database_name": "Sales", "table_names": ["Staff"]}, []),
    ],
)
def test_list_tables_filters(two_databases, filters, expected):
    ctx, *_ = two_databases

    assert [table["name"] for table in list_tables(ctx, **filters)] == expected


@pytest.mark.django_db
def test_list_tables_matches_table_ids_or_names(two_databases):
    ctx, orders, customers, staff = two_databases

    result = list_tables(
        ctx,
        database_id=orders.database_id,
        table_ids=[orders.id, staff.id],
        table_names=["Customers"],
    )

    assert [table["id"] for table in result] == [orders.id, customers.id]


@pytest.mark.django_db
def test_list_tables_over_mcp_keeps_the_list_shape(data_fixture):
    # An endpoint without an allow-list gets the legacy tools, list_tables among them.
    endpoint = data_fixture.create_mcp_endpoint()
    database = data_fixture.create_database_application(
        workspace=endpoint.workspace, name="Sales"
    )
    table = data_fixture.create_database_table(database=database, name="Orders")
    data_fixture.create_database_table(
        database=data_fixture.create_database_application(workspace=endpoint.workspace)
    )

    result = _call(endpoint, "list_tables", {"database_id": database.id})

    assert result.isError is False
    assert json.loads(result.content[0].text) == [
        {
            "id": table.id,
            "name": "Orders",
            "order": table.order,
            "database_id": database.id,
            "database_name": "Sales",
        }
    ]
