"""Tests for the field tools shared by MCP and Kuma."""

import json
from unittest.mock import patch

from django.db import IntegrityError, connection, transaction
from django.test.utils import CaptureQueriesContext

import pytest
from asgiref.sync import async_to_sync
from loguru import logger as loguru_logger
from mcp.shared.memory import (
    create_connected_server_and_client_session as client_session,
)

from baserow.contrib.database.fields.actions import (
    CreateFieldActionType,
    DeleteFieldActionType,
    UpdateFieldActionType,
)
from baserow.contrib.database.fields.models import Field
from baserow.contrib.database.table.models import Table
from baserow.contrib.database.tools.fields import (
    FieldItemCreate,
    FieldItemUpdate,
    create_fields,
    delete_fields,
    update_fields,
)
from baserow.core.mcp import BaserowMCPServer, current_key
from baserow.core.tools import ToolContext


@pytest.fixture
def table_ctx(data_fixture):
    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=user)
    database = data_fixture.create_database_application(workspace=workspace)
    table = data_fixture.create_database_table(database=database)
    data_fixture.create_text_field(table=table, name="Name", primary=True)
    return ToolContext(user=user, workspace=workspace), table


@pytest.mark.django_db
def test_create_fields_stores_a_raw_formula_unchanged(table_ctx):
    ctx, table = table_ctx

    result = create_fields(
        ctx,
        table.id,
        [FieldItemCreate(name="Joined", type="formula", formula="concat('a', 'b')")],
    )

    (created,) = result["created_fields"]
    assert created["name"] == "Joined"
    assert created["formula"] == "concat('a', 'b')"
    assert "formula_errors" not in result
    field = table.field_set.get(name="Joined").specific
    assert field.formula == "concat('a', 'b')"


@pytest.mark.django_db
def test_create_fields_reports_an_invalid_formula_without_creating_it(table_ctx):
    ctx, table = table_ctx

    result = create_fields(
        ctx,
        table.id,
        [
            FieldItemCreate(name="Notes", type="text"),
            FieldItemCreate(name="Broken", type="formula", formula="concat("),
        ],
    )

    assert [field["name"] for field in result["created_fields"]] == ["Notes"]
    (error,) = result["formula_errors"]
    assert error["table_id"] == table.id
    assert error["field_name"] == "Broken"
    assert error["formula"] == "concat("
    assert "Invalid syntax" in error["error"]
    assert not Field.objects_and_trash.filter(table=table, name="Broken").exists()


@pytest.mark.django_db
def test_create_fields_rejects_a_formula_description(table_ctx):
    ctx, table = table_ctx

    result = create_fields(
        ctx,
        table.id,
        [
            FieldItemCreate(
                name="Full name", type="formula", formula="$formula: full name"
            )
        ],
    )

    assert result["created_fields"] == []
    assert result["formula_errors"] == [
        {
            "table_id": table.id,
            "field_name": "Full name",
            "formula": "$formula: full name",
            "error": "'Full name' needs a formula, not a description. Write it in "
            "Baserow formula syntax.",
        }
    ]
    assert not table.field_set.filter(name="Full name").exists()


@pytest.mark.django_db
def test_create_fields_hides_tables_of_other_workspaces(data_fixture, table_ctx):
    ctx, _table = table_ctx
    other_table = data_fixture.create_database_table(user=ctx.user)

    with pytest.raises(Table.DoesNotExist):
        create_fields(ctx, other_table.id, [FieldItemCreate(name="X", type="text")])
    assert not other_table.field_set.filter(name="X").exists()


@pytest.mark.django_db
def test_update_fields_stores_a_raw_formula_unchanged(data_fixture, table_ctx):
    ctx, table = table_ctx
    field = data_fixture.create_formula_field(table=table, name="F", formula="'x'")

    result = update_fields(
        ctx, [FieldItemUpdate(field_id=field.id, formula="concat('a', 'b')")]
    )

    assert result["changed"] is True
    assert result["updated_fields"][0]["formula"] == "concat('a', 'b')"
    assert "formula_errors" not in result
    field.refresh_from_db()
    assert field.formula == "concat('a', 'b')"


@pytest.mark.django_db
@pytest.mark.parametrize(
    "formula,message",
    [
        ("concat(", "Invalid syntax"),
        (
            "$formula: full name",
            "'G' needs a formula, not a description. Write it in Baserow formula "
            "syntax.",
        ),
    ],
)
def test_update_fields_reports_an_invalid_formula_without_storing_it(
    data_fixture, table_ctx, formula, message
):
    ctx, table = table_ctx
    field = data_fixture.create_formula_field(table=table, name="F", formula="'x'")

    result = update_fields(
        ctx, [FieldItemUpdate(field_id=field.id, name="G", formula=formula)]
    )

    assert result["updated_fields"] == []
    assert result["changed"] is False
    (error,) = result["formula_errors"]
    assert error["table_id"] == table.id
    assert error["field_id"] == field.id
    assert error["field_name"] == "G"
    assert error["formula"] == formula
    assert message in error["error"]
    field.refresh_from_db()
    assert (field.name, field.formula) == ("F", "'x'")


@pytest.mark.django_db
def test_update_and_delete_treat_other_workspaces_as_missing(data_fixture, table_ctx):
    ctx, _table = table_ctx
    other_field = data_fixture.create_text_field(user=ctx.user, name="Other")
    missing_id = other_field.id + 1000

    updated = update_fields(
        ctx,
        [
            FieldItemUpdate(field_id=other_field.id, name="Renamed"),
            FieldItemUpdate(field_id=missing_id, name="Renamed"),
        ],
    )
    deleted = delete_fields(ctx, [other_field.id, missing_id])

    assert updated["errors"] == [
        f"Error updating field {other_field.id}: The field with id "
        f"{other_field.id} does not exist.",
        f"Error updating field {missing_id}: The field with id {missing_id} "
        "does not exist.",
    ]
    assert deleted["deleted_field_ids"] == []
    assert deleted["errors"] == [
        f"Error deleting field {other_field.id}: The field with id "
        f"{other_field.id} does not exist.",
        f"Error deleting field {missing_id}: The field with id {missing_id} "
        "does not exist.",
    ]
    other_field.refresh_from_db()
    assert other_field.name == "Other"
    assert not other_field.trashed


@pytest.mark.django_db
def test_delete_fields_trashes_the_fields(data_fixture, table_ctx):
    ctx, table = table_ctx
    field = data_fixture.create_text_field(table=table, name="Old")

    result = delete_fields(ctx, [field.id])

    assert result == {"deleted_field_ids": [field.id]}
    assert Field.objects_and_trash.get(id=field.id).trashed


def _fail_after_doing(action_type, should_fail):
    """
    Patch an action's `do` so it applies the change and then raises, as a
    database error in the middle of an item would.
    """

    original = action_type.do

    def do(user, *args, **kwargs):
        result = original(user, *args, **kwargs)
        if should_fail(args, kwargs):
            raise IntegrityError("duplicate key value")
        return result

    return patch.object(action_type, "do", side_effect=do)


@pytest.mark.django_db
def test_create_fields_keeps_the_other_fields_when_one_fails(table_ctx):
    ctx, table = table_ctx

    with _fail_after_doing(CreateFieldActionType, lambda a, k: k["name"] == "Two"):
        result = create_fields(
            ctx,
            table.id,
            [
                FieldItemCreate(name="One", type="text"),
                FieldItemCreate(name="Two", type="text"),
                FieldItemCreate(name="Three", type="text"),
            ],
        )

    assert [f["name"] for f in result["created_fields"]] == ["One", "Three"]
    (error,) = result["field_errors"]
    assert "Error creating field Two" in error
    assert set(table.field_set.values_list("name", flat=True)) == {
        "Name",
        "One",
        "Three",
    }


@pytest.mark.django_db
def test_update_fields_keeps_the_other_updates_when_one_fails(data_fixture, table_ctx):
    ctx, table = table_ctx
    fields = [
        data_fixture.create_text_field(table=table, name=name)
        for name in ("One", "Two", "Three")
    ]

    with _fail_after_doing(UpdateFieldActionType, lambda a, k: a[0].id == fields[1].id):
        result = update_fields(
            ctx,
            [FieldItemUpdate(field_id=f.id, name=f"{f.name} new") for f in fields],
        )

    assert [f["id"] for f in result["updated_fields"]] == [
        fields[0].id,
        fields[2].id,
    ]
    (error,) = result["errors"]
    assert error.startswith(f"Error updating field {fields[1].id}")
    assert [Field.objects.get(id=f.id).name for f in fields] == [
        "One new",
        "Two",
        "Three new",
    ]


@pytest.mark.django_db
def test_delete_fields_keeps_the_other_deletes_when_one_fails(data_fixture, table_ctx):
    ctx, table = table_ctx
    fields = [
        data_fixture.create_text_field(table=table, name=name)
        for name in ("One", "Two", "Three")
    ]

    with _fail_after_doing(DeleteFieldActionType, lambda a, k: a[0].id == fields[1].id):
        result = delete_fields(ctx, [f.id for f in fields])

    assert result["deleted_field_ids"] == [fields[0].id, fields[2].id]
    (error,) = result["errors"]
    assert error.startswith(f"Error deleting field {fields[1].id}")
    assert [Field.objects_and_trash.get(id=f.id).trashed for f in fields] == [
        True,
        False,
        True,
    ]


@pytest.fixture
def error_records():
    records = []
    handler_id = loguru_logger.add(
        lambda m: records.append(m.record), level="ERROR", format="{message}"
    )
    yield records
    loguru_logger.remove(handler_id)


def _raise_unexpected(*args, **kwargs):
    raise RuntimeError("relation secret_table does not exist")


@pytest.mark.django_db
@pytest.mark.parametrize(
    "action_type,run,errors_key",
    [
        (
            CreateFieldActionType,
            lambda ctx, table, field: create_fields(
                ctx, table.id, [FieldItemCreate(name="New", type="text")]
            ),
            "field_errors",
        ),
        (
            UpdateFieldActionType,
            lambda ctx, table, field: update_fields(
                ctx, [FieldItemUpdate(field_id=field.id, name="Renamed")]
            ),
            "errors",
        ),
        (
            DeleteFieldActionType,
            lambda ctx, table, field: delete_fields(ctx, [field.id]),
            "errors",
        ),
    ],
)
def test_field_tools_log_an_unexpected_error_and_hide_its_message(
    data_fixture, table_ctx, error_records, action_type, run, errors_key
):
    ctx, table = table_ctx
    field = data_fixture.create_text_field(table=table, name="Old")

    with patch.object(action_type, "do", side_effect=_raise_unexpected):
        result = run(ctx, table, field)

    (error,) = result[errors_key]
    assert "Internal error." in error
    assert "secret_table" not in error
    (record,) = error_records
    assert record["exception"].type is RuntimeError


@pytest.mark.django_db
def test_field_tools_keep_the_message_of_an_expected_error(
    data_fixture, table_ctx, error_records
):
    ctx, table = table_ctx
    field = data_fixture.create_text_field(table=table, name="Old")
    primary = table.field_set.get(primary=True)

    created = create_fields(ctx, table.id, [FieldItemCreate(name="Old", type="text")])
    updated = update_fields(ctx, [FieldItemUpdate(field_id=field.id, name="Name")])
    deleted = delete_fields(ctx, [primary.id])

    (create_error,) = created["field_errors"]
    assert (
        f"A field already exists for table '{table.name}' with the name 'Old'."
        in create_error
    )
    assert updated["errors"] == [
        f"Error updating field {field.id}: A field already exists for table "
        f"'{table.name}' with the name 'Name'."
    ]
    assert deleted["errors"] == [
        f"Error deleting field {primary.id}: Cannot delete the primary field of "
        "a table."
    ]
    assert error_records == []


@pytest.mark.django_db
@pytest.mark.parametrize("formula", [None, "", "  "])
def test_create_fields_reports_a_formula_field_without_a_formula(table_ctx, formula):
    ctx, table = table_ctx
    item = {"name": "Total", "type": "formula"}
    if formula is not None:
        item["formula"] = formula

    result = create_fields(ctx, table.id, [FieldItemCreate(**item)])

    assert result["created_fields"] == []
    assert "field_errors" not in result
    assert result["formula_errors"] == [
        {
            "table_id": table.id,
            "field_name": "Total",
            "formula": formula or "",
            "error": "'Total' needs a formula.",
        }
    ]
    assert not Field.objects_and_trash.filter(table=table, name="Total").exists()


@pytest.mark.django_db
def test_update_fields_reports_an_empty_formula(data_fixture, table_ctx):
    ctx, table = table_ctx
    field = data_fixture.create_formula_field(table=table, name="F", formula="'x'")

    result = update_fields(ctx, [FieldItemUpdate(field_id=field.id, formula="")])

    assert result["updated_fields"] == []
    assert "errors" not in result
    assert result["formula_errors"] == [
        {
            "field_id": field.id,
            "table_id": table.id,
            "field_name": "F",
            "formula": "",
            "error": "'F' needs a formula.",
        }
    ]
    field.refresh_from_db()
    assert field.formula == "'x'"


def test_create_fields_schema_has_no_default_formula():
    schema = FieldItemCreate.model_json_schema()["properties"]["formula"]

    assert schema.get("default") is None


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


FIELD_TOOLS = ["create_fields", "update_fields", "delete_fields"]


@pytest.mark.django_db
def test_field_tools_over_mcp(data_fixture):
    endpoint = data_fixture.create_mcp_endpoint(allowed_tools=FIELD_TOOLS)
    database = data_fixture.create_database_application(workspace=endpoint.workspace)
    table = data_fixture.create_database_table(database=database)

    created = _call(
        endpoint,
        "create_fields",
        {"table_id": table.id, "fields": [{"name": "Status", "type": "text"}]},
    )
    field_id = json.loads(created.content[0].text)["created_fields"][0]["id"]
    updated = _call(
        endpoint,
        "update_fields",
        {"fields": [{"field_id": field_id, "name": "State"}]},
    )
    deleted = _call(endpoint, "delete_fields", {"field_ids": [field_id]})

    assert created.isError is False
    assert json.loads(updated.content[0].text)["updated_fields"][0]["name"] == "State"
    assert json.loads(deleted.content[0].text) == {"deleted_field_ids": [field_id]}
    assert Field.objects_and_trash.get(id=field_id).trashed


@pytest.mark.django_db
def test_create_fields_over_mcp_table_in_other_workspace_is_not_found(data_fixture):
    endpoint = data_fixture.create_mcp_endpoint(allowed_tools=FIELD_TOOLS)
    other_table = data_fixture.create_database_table(user=endpoint.user)

    result = _call(
        endpoint,
        "create_fields",
        {"table_id": other_table.id, "fields": [{"name": "X", "type": "text"}]},
    )

    assert result.isError is True
    assert result.content[0].text == "Not found in this workspace."
    assert not other_table.field_set.filter(name="X").exists()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "tool,arguments,verb",
    [
        (
            "update_fields",
            lambda field_id: {"fields": [{"field_id": field_id, "name": "Renamed"}]},
            "updating",
        ),
        ("delete_fields", lambda field_id: {"field_ids": [field_id]}, "deleting"),
    ],
)
def test_field_tools_over_mcp_treat_other_workspaces_as_missing(
    data_fixture, tool, arguments, verb
):
    endpoint = data_fixture.create_mcp_endpoint(allowed_tools=FIELD_TOOLS)
    other_field = data_fixture.create_text_field(user=endpoint.user, name="Other")
    missing_id = other_field.id + 1000

    other = json.loads(_call(endpoint, tool, arguments(other_field.id)).content[0].text)
    missing = json.loads(_call(endpoint, tool, arguments(missing_id)).content[0].text)

    def error(field_id):
        return (
            f"Error {verb} field {field_id}: The field with id {field_id} does "
            "not exist."
        )

    assert other["errors"] == [error(other_field.id)]
    assert missing["errors"] == [error(missing_id)]
    other_field.refresh_from_db()
    assert other_field.name == "Other"
    assert not other_field.trashed


@pytest.mark.django_db
def test_update_fields_locks_the_field_like_the_rest_api(data_fixture, table_ctx):
    ctx, table = table_ctx
    field = data_fixture.create_single_select_field(table=table, name="Status")

    with CaptureQueriesContext(connection) as queries:
        update_fields(
            ctx, [FieldItemUpdate(field_id=field.id, add_options=[{"value": "New"}])]
        )

    locks = [
        q["sql"]
        for q in queries.captured_queries
        if "FOR UPDATE" in q["sql"] and '"database_field"' in q["sql"]
    ]
    assert locks
    assert list(field.select_options.values_list("value", flat=True)) == ["New"]


def _field_names(table):
    model = Table.objects.get(id=table.id).get_model()
    return sorted(f["field"].name for f in model._field_objects.values())


@pytest.mark.django_db
def test_update_fields_drops_the_model_cached_in_a_failed_update(
    data_fixture, table_ctx
):
    ctx, table = table_ctx
    field = data_fixture.create_number_field(table=table, name="Num")

    with _fail_after_doing(UpdateFieldActionType, lambda a, k: True):
        update_fields(ctx, [FieldItemUpdate(field_id=field.id, name="Renamed")])

    assert _field_names(table) == ["Name", "Num"]


@pytest.mark.django_db
def test_delete_fields_drops_the_model_cached_in_a_failed_delete(
    data_fixture, table_ctx
):
    ctx, table = table_ctx
    field = data_fixture.create_number_field(table=table, name="Num")

    with _fail_after_doing(DeleteFieldActionType, lambda a, k: True):
        delete_fields(ctx, [field.id])

    assert _field_names(table) == ["Name", "Num"]


@pytest.fixture
def linked_tables(data_fixture, table_ctx):
    ctx, table = table_ctx
    other = data_fixture.create_database_table(database=table.database, name="Other")
    data_fixture.create_text_field(table=other, name="Title", primary=True)
    return ctx, table, other


@pytest.mark.django_db
@pytest.mark.parametrize("key", ["through_field", "through_field_id"])
def test_create_fields_looks_up_through_the_named_link_field(
    data_fixture, linked_tables, key
):
    ctx, table, other = linked_tables
    data_fixture.create_link_row_field(table=table, name="First", link_row_table=other)
    second = data_fixture.create_link_row_field(
        table=table, name="Second", link_row_table=other
    )

    result = create_fields(
        ctx,
        table.id,
        [
            FieldItemCreate(
                **{"name": "Titles", "type": "lookup", key: second.id},
                target_field="Title",
            )
        ],
    )

    assert "field_errors" not in result
    (created,) = result["created_fields"]
    assert created["through_field"] == second.id
    assert table.field_set.get(name="Titles").specific.through_field_id == second.id


@pytest.mark.django_db
def test_create_fields_looks_up_through_a_link_field_named_by_name(
    data_fixture, linked_tables
):
    ctx, table, other = linked_tables
    link = data_fixture.create_link_row_field(
        table=table, name="Link", link_row_table=other
    )

    result = create_fields(
        ctx,
        table.id,
        [
            FieldItemCreate(
                name="Titles", type="lookup", through_field="Link", target_field="Title"
            )
        ],
    )

    assert [f["through_field"] for f in result["created_fields"]] == [link.id]


@pytest.mark.django_db
def test_create_fields_reports_a_through_field_that_is_no_link_of_the_table(
    data_fixture, linked_tables
):
    ctx, table, other = linked_tables
    text = data_fixture.create_text_field(table=table, name="Notes")

    result = create_fields(
        ctx,
        table.id,
        [
            FieldItemCreate(
                name="Titles",
                type="lookup",
                through_field=text.id,
                target_field="Title",
            )
        ],
    )

    assert result["created_fields"] == []
    (error,) = result["field_errors"]
    assert f"has no link_row field '{text.id}' for lookup 'Titles'" in error
    assert set(table.field_set.values_list("name", flat=True)) == {"Name", "Notes"}


@pytest.mark.django_db
def test_create_fields_returns_the_link_field_a_lookup_creates(linked_tables):
    ctx, table, other = linked_tables

    result = create_fields(
        ctx,
        table.id,
        [
            FieldItemCreate(
                name="Titles", type="lookup", linked_table="Other", target_field="Title"
            )
        ],
    )

    link, lookup = result["created_fields"]
    assert (link["name"], link["type"], link["linked_table"]) == (
        "Other",
        "link_row",
        other.id,
    )
    assert (lookup["name"], lookup["through_field"]) == ("Titles", link["id"])
