"""
Errors raised by a tool reach the client as an MCP error result. Expected ones are
not logged as errors, only unexpected ones are.
"""

import logging
from unittest.mock import patch

from django.core.exceptions import ObjectDoesNotExist

import pytest
from asgiref.sync import async_to_sync
from loguru import logger as loguru_logger
from mcp.shared.memory import (
    create_connected_server_and_client_session as client_session,
)
from pydantic import TypeAdapter, ValidationError
from pydantic_ai import ModelRetry

from baserow.contrib.builder.pages.exceptions import PageDoesNotExist
from baserow.core.exceptions import (
    ApplicationDoesNotExist,
    PermissionException,
    UserNotInWorkspace,
)
from baserow.core.mcp import BaserowMCPServer, current_key
from baserow.core.mcp.registries import MCPTool, mcp_tool_registry

TOOLS = ["list_pages", "list_nodes", "boom_tool"]


class BoomTool(MCPTool):
    """Raises whatever is set in ``raises``."""

    type = "boom_tool"
    raises: Exception = RuntimeError("secret internals")

    async def call(self, endpoint, call_arguments):
        raise self.raises


@pytest.fixture
def boom_tool():
    mcp_tool_registry.register(BoomTool())
    yield mcp_tool_registry.get("boom_tool")
    mcp_tool_registry.registry.pop("boom_tool")


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

    return async_to_sync(inner)()


def _assert_no_error_logged(caplog, error_records):
    assert [r for r in caplog.records if r.levelno >= logging.ERROR] == []
    assert error_records == []


@pytest.fixture
def setup(data_fixture):
    user = data_fixture.create_user()
    mine = data_fixture.create_workspace(user=user)
    other = data_fixture.create_workspace(user=user)
    endpoint = data_fixture.create_mcp_endpoint(
        user=user, workspace=mine, allowed_tools=TOOLS
    )
    return user, mine, other, endpoint


@pytest.mark.django_db(transaction=True)
def test_other_workspace_is_an_error_result(data_fixture, setup, caplog, error_records):
    user, mine, other, endpoint = setup
    builder = data_fixture.create_builder_application(user=user, workspace=other)

    result = _call(endpoint, "list_pages", {"application_id": builder.id})

    assert result.isError is True
    assert "not found" in result.content[0].text.lower()
    _assert_no_error_logged(caplog, error_records)


@pytest.mark.django_db(transaction=True)
def test_wrong_argument_type_names_the_argument(
    data_fixture, setup, caplog, error_records
):
    user, mine, other, endpoint = setup

    result = _call(endpoint, "list_pages", {"application_id": "abc"})

    assert result.isError is True
    assert "application_id" in result.content[0].text
    assert "Internal error" not in result.content[0].text
    _assert_no_error_logged(caplog, error_records)


@pytest.mark.django_db(transaction=True)
def test_validation_error_inside_a_tool_body_is_internal(
    data_fixture, setup, caplog, error_records
):
    user, mine, other, endpoint = setup
    builder = data_fixture.create_builder_application(user=user, workspace=mine)
    try:
        TypeAdapter(int).validate_python("abc")
    except ValidationError as exc:
        body_error = exc

    with patch(
        "baserow_enterprise.assistant.tools.builder.helpers.list_pages",
        side_effect=body_error,
    ):
        result = _call(endpoint, "list_pages", {"application_id": builder.id})

    assert result.isError is True
    assert result.content[0].text == "Internal error."
    assert len(error_records) == 1


@pytest.mark.django_db(transaction=True)
def test_missing_argument_names_the_argument(
    data_fixture, setup, caplog, error_records
):
    user, mine, other, endpoint = setup

    result = _call(endpoint, "list_pages", {})

    assert result.isError is True
    assert "application_id" in result.content[0].text
    _assert_no_error_logged(caplog, error_records)


@pytest.mark.django_db(transaction=True)
def test_model_retry_message_is_returned(data_fixture, setup, caplog, error_records):
    user, mine, other, endpoint = setup
    builder = data_fixture.create_builder_application(user=user, workspace=mine)

    with patch(
        "baserow_enterprise.assistant.tools.builder.helpers.list_pages",
        side_effect=ModelRetry("Use a page name"),
    ):
        result = _call(endpoint, "list_pages", {"application_id": builder.id})

    assert result.isError is True
    assert "Use a page name" in result.content[0].text
    _assert_no_error_logged(caplog, error_records)


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    "exc,expected",
    [
        (
            PermissionException(),
            "You don't have permission to do this in this workspace.",
        ),
        (UserNotInWorkspace(), "Not found in this workspace."),
        (
            ApplicationDoesNotExist(),
            "Not found in this workspace.",
        ),
        (
            PageDoesNotExist(),
            "Not found in this workspace.",
        ),
        (
            ObjectDoesNotExist(),
            "Not found in this workspace.",
        ),
    ],
)
def test_mapped_exceptions(setup, boom_tool, caplog, error_records, exc, expected):
    user, mine, other, endpoint = setup
    boom_tool.raises = exc

    result = _call(endpoint, "boom_tool", {})

    assert result.isError is True
    assert result.content[0].text == expected
    _assert_no_error_logged(caplog, error_records)


@pytest.mark.django_db(transaction=True)
def test_unexpected_exception_is_logged_and_hidden(
    setup, boom_tool, caplog, error_records
):
    user, mine, other, endpoint = setup

    result = _call(endpoint, "boom_tool", {})

    assert result.isError is True
    assert result.content[0].text == "Internal error."
    assert "secret internals" not in result.content[0].text
    assert len(error_records) == 1
    assert error_records[0]["exception"] is not None


@pytest.mark.django_db(transaction=True)
def test_failure_event_is_still_captured(setup, boom_tool):
    user, mine, other, endpoint = setup
    boom_tool.raises = PermissionException()

    with patch.object(BaserowMCPServer, "capture_event") as capture:
        _call(endpoint, "boom_tool", {})

    capture.assert_called_once()
    assert capture.call_args.args[1:] == (
        "mcp_tool_called",
        {"tool": "boom_tool", "success": False},
    )


@pytest.mark.django_db(transaction=True)
def test_missing_and_foreign_workflow_give_identical_errors(
    data_fixture, setup, caplog, error_records
):
    user, mine, other, endpoint = setup
    automation = data_fixture.create_automation_application(user=user, workspace=other)
    foreign = data_fixture.create_automation_workflow(automation=automation)

    foreign_result = _call(endpoint, "list_nodes", {"workflow_id": foreign.id})
    missing_result = _call(endpoint, "list_nodes", {"workflow_id": foreign.id + 9999})

    assert foreign_result.isError is True
    assert missing_result.isError is True
    assert foreign_result.content[0].text == missing_result.content[0].text
    _assert_no_error_logged(caplog, error_records)


@pytest.mark.django_db(transaction=True)
def test_foreign_workflow_without_read_access_looks_missing(
    data_fixture,
    enterprise_data_fixture,
    enable_enterprise,
    setup,
    caplog,
    error_records,
):
    user, mine, other, endpoint = setup
    # The user belongs to the other workspace but has no access there.
    other.users.through.objects.filter(user=user, workspace=other).update(
        permissions="NO_ACCESS"
    )
    automation = data_fixture.create_automation_application(workspace=other)
    foreign = data_fixture.create_automation_workflow(automation=automation)

    foreign_result = _call(endpoint, "list_nodes", {"workflow_id": foreign.id})
    missing_result = _call(endpoint, "list_nodes", {"workflow_id": foreign.id + 9999})

    assert foreign_result.isError is True
    assert foreign_result.content[0].text == missing_result.content[0].text
    assert "permission" not in foreign_result.content[0].text
    _assert_no_error_logged(caplog, error_records)
