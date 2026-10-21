"""Tests for the field tools shared by MCP and Kuma."""

import pytest

from baserow.contrib.database.fields.models import Field
from baserow.contrib.database.table.models import Table
from baserow.contrib.database.tools.fields import (
    FieldItemCreate,
    FieldItemUpdate,
    create_fields,
    delete_fields,
    update_fields,
)
from baserow.core.tools import ToolContext


@pytest.fixture(autouse=True)
def no_formula_fixer(monkeypatch):
    """The shared path never calls a model, so the Kuma fixer must stay unused."""

    def fail(*args, **kwargs):
        raise AssertionError("The shared field tools must not call a model.")

    monkeypatch.setattr(
        "baserow_enterprise.assistant.tools.database.agents.make_formula_fixer", fail
    )


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
