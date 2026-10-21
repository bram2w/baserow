"""Tests for the field tools shared by MCP and Kuma."""

from unittest.mock import patch

from django.db import IntegrityError

import pytest

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
