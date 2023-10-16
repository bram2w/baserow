# noinspection PyPep8Naming

import pytest


# noinspection PyPep8Naming
@pytest.mark.once_per_day_in_ci
def test_forwards_migration(data_fixture, migrator, teardown_table_metadata):
    migrate_from = [
        ("database", "0039_formulafield"),
        ("core", "0010_fix_trash_constraint"),
    ]
    migrate_to = [("database", "0040_formulafield_remove_field_by_id")]

    old_state = migrator.migrate(migrate_from)

    # The models used by the data_fixture below are not touched by this migration so
    # it is safe to use the latest version in the test.
    ContentType = old_state.apps.get_model("contenttypes", "ContentType")
    Group = old_state.apps.get_model("core", "Group")
    Database = old_state.apps.get_model("database", "Database")
    Table = old_state.apps.get_model("database", "Table")

    content_type = ContentType.objects.get_for_model(Database)
    group = Group(name="group")
    group.trashed = False
    group.save()
    database = Database.objects.create(
        content_type=content_type, order=1, name="test", group=group, trashed=False
    )
    table = Table.objects.create(
        database=database, name="table", order=1, trashed=False
    )

    TextField = old_state.apps.get_model("database", "TextField")
    text_field_content_type = ContentType.objects.get_for_model(TextField)
    text_field = TextField.objects.create(
        name="text",
        primary=True,
        table=table,
        order=1,
        content_type=text_field_content_type,
    )

    FormulaField = old_state.apps.get_model("database", "FormulaField")
    content_type_id = ContentType.objects.get_for_model(FormulaField).id
    formula_field = FormulaField.objects.create(
        table_id=table.id,
        formula_type="text",
        formula=f"field_by_id({text_field.id})",
        content_type_id=content_type_id,
        order=0,
        name="a",
    )
    unknown_field_by_id = FormulaField.objects.create(
        table_id=table.id,
        formula_type="text",
        formula=f"field_by_id(9999)",
        content_type_id=content_type_id,
        order=0,
        name="b",
    )

    new_state = migrator.migrate(migrate_to)
    NewFormulaField = new_state.apps.get_model("database", "FormulaField")

    new_formula_field = NewFormulaField.objects.get(id=formula_field.id)
    assert new_formula_field.formula == "field('text')"
    assert (
        new_formula_field.old_formula_with_field_by_id
        == f"field_by_id({text_field.id})"
    )
    new_unknown_field_by_id = NewFormulaField.objects.get(id=unknown_field_by_id.id)
    assert new_unknown_field_by_id.formula == "field('unknown field 9999')"
    assert new_unknown_field_by_id.old_formula_with_field_by_id == f"field_by_id(9999)"


# noinspection PyPep8Naming
@pytest.mark.once_per_day_in_ci
def test_backwards_migration(data_fixture, migrator, teardown_table_metadata):
    migrate_from = [
        ("database", "0040_formulafield_remove_field_by_id"),
        ("core", "0010_fix_trash_constraint"),
    ]
    migrate_to = [("database", "0039_formulafield")]

    old_state = migrator.migrate(migrate_from)

    # The models used by the data_fixture below are not touched by this migration so
    # it is safe to use the latest version in the test.
    ContentType = old_state.apps.get_model("contenttypes", "ContentType")
    Group = old_state.apps.get_model("core", "Group")
    Database = old_state.apps.get_model("database", "Database")
    Table = old_state.apps.get_model("database", "Table")

    content_type = ContentType.objects.get_for_model(Database)
    group = Group(name="group")
    group.trashed = False
    group.save()
    database = Database.objects.create(
        content_type_id=content_type.id,
        order=1,
        name="test",
        group_id=group.id,
        trashed=False,
    )
    table = Table.objects.create(
        database_id=database.id, name="table", order=1, trashed=False
    )

    TextField = old_state.apps.get_model("database", "TextField")
    text_field_content_type = ContentType.objects.get_for_model(TextField)
    text_field = TextField.objects.create(
        name="text",
        primary=True,
        table_id=table.id,
        order=1,
        content_type_id=text_field_content_type.id,
    )

    FormulaField = old_state.apps.get_model("database", "FormulaField")
    content_type_id = ContentType.objects.get_for_model(FormulaField).id
    formula_field = FormulaField.objects.create(
        table_id=table.id,
        formula_type="text",
        formula=f"field('text')",
        content_type_id=content_type_id,
        order=0,
        name="a",
    )
    unknown_field = FormulaField.objects.create(
        table_id=table.id,
        formula_type="text",
        formula=f"field('unknown')",
        content_type_id=content_type_id,
        order=0,
        name="b",
    )

    new_state = migrator.migrate(migrate_to)
    NewFormulaField = new_state.apps.get_model("database", "FormulaField")

    new_formula_field = NewFormulaField.objects.get(id=formula_field.id)
    assert new_formula_field.formula == f"field_by_id({text_field.id})"
    new_unknown_field_by_id = NewFormulaField.objects.get(id=unknown_field.id)
    assert new_unknown_field_by_id.formula == "field('unknown')"
