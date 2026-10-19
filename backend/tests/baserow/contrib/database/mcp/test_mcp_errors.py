"""
Database tool input mistakes reach the client as readable error results and are not
logged as errors.
"""

import logging

from django.db import transaction

import pytest
from asgiref.sync import async_to_sync
from loguru import logger as loguru_logger
from mcp.shared.memory import (
    create_connected_server_and_client_session as client_session,
)

from baserow.core.mcp import BaserowMCPServer, current_key
from baserow.core.mcp.constants import LEGACY_DEFAULT_TOOLS
from baserow.core.mcp.registries import mcp_tool_registry

WRITE_TOOLS = ["create_fields", "create_rows", "update_rows", "delete_rows"]


@pytest.fixture(autouse=True)
def enable_field_tools(monkeypatch):
    monkeypatch.setattr(mcp_tool_registry.get("create_fields"), "enabled", True)
    monkeypatch.setattr(
        "baserow.core.mcp.registries.LEGACY_DEFAULT_TOOLS",
        [*LEGACY_DEFAULT_TOOLS, "create_fields"],
    )


@pytest.fixture
def error_records():
    records = []
    handler_id = loguru_logger.add(
        lambda m: records.append(m.record), level="ERROR", format="{message}"
    )
    yield records
    loguru_logger.remove(handler_id)


def _call(endpoint, name, arguments):
    async def inner():
        server = BaserowMCPServer()
        token = current_key.set(endpoint.key)
        try:
            async with client_session(server._mcp_server) as client:
                return await client.call_tool(name, arguments)
        finally:
            current_key.reset(token)

    with transaction.atomic():
        return async_to_sync(inner)()


def _assert_readable_error(result, caplog, error_records, *expected):
    text = result.content[0].text
    assert result.isError is True
    assert "Internal error" not in text
    assert "Not found" not in text
    for part in expected:
        assert part.lower() in text.lower(), text
    assert [r for r in caplog.records if r.levelno >= logging.ERROR] == []
    assert error_records == []


@pytest.fixture
def table_setup(data_fixture):
    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=user)
    endpoint = data_fixture.create_mcp_endpoint(user=user, workspace=workspace)
    database = data_fixture.create_database_application(workspace=workspace)
    table = data_fixture.create_database_table(database=database)
    return data_fixture, endpoint, table


@pytest.mark.django_db
def test_invalid_single_select_value(table_setup, caplog, error_records):
    data_fixture, endpoint, table = table_setup
    data_fixture.create_text_field(table=table, name="Name", primary=True)
    field = data_fixture.create_single_select_field(table=table, name="Status")
    data_fixture.create_select_option(field=field, value="Open")

    result = _call(
        endpoint,
        "create_rows",
        {"table_id": table.id, "rows": [{"Status": "NoSuchOption"}]},
    )

    _assert_readable_error(result, caplog, error_records, "NoSuchOption")


@pytest.mark.django_db
def test_unknown_field_type(table_setup, caplog, error_records):
    data_fixture, endpoint, table = table_setup

    result = _call(
        endpoint,
        "create_fields",
        {"table_id": table.id, "fields": [{"name": "X", "type": "nonsense"}]},
    )

    _assert_readable_error(result, caplog, error_records, "nonsense")


@pytest.mark.django_db
def test_duplicate_field_name(table_setup, caplog, error_records):
    data_fixture, endpoint, table = table_setup
    data_fixture.create_text_field(table=table, name="Name", primary=True)

    result = _call(
        endpoint,
        "create_fields",
        {"table_id": table.id, "fields": [{"name": "Name", "type": "text"}]},
    )

    _assert_readable_error(result, caplog, error_records, "already exists")


@pytest.mark.django_db
def test_reserved_field_name(table_setup, caplog, error_records):
    data_fixture, endpoint, table = table_setup

    result = _call(
        endpoint,
        "create_fields",
        {"table_id": table.id, "fields": [{"name": "id", "type": "text"}]},
    )

    _assert_readable_error(result, caplog, error_records, "reserved")


@pytest.mark.django_db
def test_missing_row_names_the_ids(table_setup, caplog, error_records):
    data_fixture, endpoint, table = table_setup
    data_fixture.create_text_field(table=table, name="Name", primary=True)

    result = _call(
        endpoint, "update_rows", {"table_id": table.id, "rows": [{"id": 9999}]}
    )

    _assert_readable_error(result, caplog, error_records, "9999")


def test_to_mcp_error_flattens_validation_errors():
    from django.core.exceptions import ValidationError as DjangoValidationError

    from rest_framework.exceptions import ValidationError as DRFValidationError

    from baserow.api.exceptions import RequestBodyValidationException
    from baserow.core.mcp.exceptions import to_mcp_error

    assert "Bad" in to_mcp_error(DjangoValidationError("Bad"))
    drf = to_mcp_error(DRFValidationError({"Status": ["Nope."]}))
    assert "Status: Nope." in drf
    body = to_mcp_error(
        RequestBodyValidationException({"items": [{"name": ["Required."]}]})
    )
    assert "items.0.name: Required." in body
