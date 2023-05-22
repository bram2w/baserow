# noinspection PyPep8Naming
import pytest


@pytest.mark.once_per_day_in_ci
def test_forwards_migration(data_fixture, migrator, teardown_table_metadata):
    migrate_from = [("database", "0043_webhooks"), ("core", "0012_add_trashed_indexes")]
    migrate_to = [("database", "0044_field_dependencies")]

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
        content_type=content_type,
        order=1,
        name="test",
        group_id=group.id,
        trashed=False,
    )
    table = Table.objects.create(
        database_id=database.id, name="table", order=1, trashed=False
    )

    other_table = Table.objects.create(
        database_id=database.id, name="other table", order=1, trashed=False
    )

    TextField = old_state.apps.get_model("database", "TextField")
    text_field_content_type = ContentType.objects.get_for_model(TextField)
    other_text_field = TextField.objects.create(
        name="text",
        primary=True,
        table_id=other_table.id,
        order=1,
        content_type_id=text_field_content_type.id,
    )
    text_field = TextField.objects.create(
        name="text",
        primary=True,
        table_id=table.id,
        order=1,
        content_type_id=text_field_content_type.id,
    )

    FormulaField = old_state.apps.get_model("database", "FormulaField")
    LinkRowField = old_state.apps.get_model("database", "LinkRowField")
    formula_content_type_id = ContentType.objects.get_for_model(FormulaField).id
    link_row_content_type_id = ContentType.objects.get_for_model(LinkRowField).id
    empty_formula_field = FormulaField.objects.create(
        table_id=table.id,
        formula_type="text",
        formula=f"'a'",
        content_type_id=formula_content_type_id,
        order=0,
        name="empty",
    )
    formula_field = FormulaField.objects.create(
        table_id=table.id,
        formula_type="text",
        formula=f"field('{text_field.name}')",
        content_type_id=formula_content_type_id,
        order=0,
        name="a",
    )
    trashed_field = FormulaField.objects.create(
        table_id=table.id,
        formula_type="text",
        formula=f"1",
        content_type_id=formula_content_type_id,
        order=0,
        name="trashed",
        trashed=True,
    )
    sub_formula_field = FormulaField.objects.create(
        table_id=table.id,
        formula_type="text",
        formula=f"field('{formula_field.name}')",
        content_type_id=formula_content_type_id,
        order=0,
        name="c",
    )
    unknown_field = FormulaField.objects.create(
        table_id=table.id,
        formula_type="invalid",
        formula=f"field('{trashed_field.name}')",
        content_type_id=formula_content_type_id,
        order=0,
        name="b",
    )
    link_row_field = LinkRowField.objects.create(
        table_id=table.id,
        content_type_id=link_row_content_type_id,
        link_row_table_id=other_table.id,
        name="link",
        order=1,
    )
    related_link_row_field = LinkRowField.objects.create(
        table_id=table.id,
        content_type_id=link_row_content_type_id,
        link_row_table_id=table.id,
        link_row_related_field=link_row_field,
        name="other_side_of_link",
        order=0,
    )
    link_row_field.link_row_related_field = related_link_row_field
    link_row_field.save()

    new_state = migrator.migrate(
        migrate_to,
    )
    NewFormulaField = new_state.apps.get_model("database", "FormulaField")
    NewLinkRowField = new_state.apps.get_model("database", "LinkRowField")

    new_formula_field = NewFormulaField.objects.get(id=formula_field.id)
    new_sub_formula_field = NewFormulaField.objects.get(id=sub_formula_field.id)
    new_empty_formula_field = NewFormulaField.objects.get(id=empty_formula_field.id)

    def _unwrap_ids(qs):
        return list(qs.values_list("id", flat=True))

    assert _unwrap_ids(new_empty_formula_field.field_dependencies) == []
    assert _unwrap_ids(new_formula_field.field_dependencies) == [text_field.id]
    assert _unwrap_ids(new_formula_field.dependant_fields) == [new_sub_formula_field.id]
    assert _unwrap_ids(new_sub_formula_field.field_dependencies) == [
        new_formula_field.id
    ]
    assert _unwrap_ids(new_sub_formula_field.dependant_fields) == []

    assert new_formula_field.formula == formula_field.formula
    assert new_sub_formula_field.formula == new_sub_formula_field.formula

    new_unknown_field = NewFormulaField.objects.get(id=unknown_field.id)
    assert new_unknown_field.formula == unknown_field.formula
    assert not new_unknown_field.field_dependencies.exists()
    assert not new_unknown_field.dependant_fields.exists()
    assert new_unknown_field.dependencies.count() == 1
    assert (
        new_unknown_field.dependencies.first().broken_reference_field_name == "trashed"
    )

    new_link_row_field = NewLinkRowField.objects.get(id=link_row_field.id)
    new_related_link_row_field = NewLinkRowField.objects.get(
        id=related_link_row_field.id
    )
    assert _unwrap_ids(new_link_row_field.field_dependencies) == [other_text_field.id]
    # The link row field depends on the second tables primary field via itself
    first_via = new_link_row_field.vias.get()
    assert first_via.via == new_link_row_field
    assert first_via.dependant.id == new_link_row_field.id
    assert first_via.dependency.id == other_text_field.id
    assert _unwrap_ids(new_related_link_row_field.field_dependencies) == [text_field.id]
    # The related link row field depends on the first tables primary field via itself
    second_via = new_related_link_row_field.vias.get()
    assert second_via.via == new_related_link_row_field
    assert second_via.dependant.id == new_related_link_row_field.id
    assert second_via.dependency.id == text_field.id


# noinspection PyPep8Naming
@pytest.mark.once_per_day_in_ci
def test_backwards_migration(data_fixture, migrator, teardown_table_metadata):
    migrate_from = [
        ("database", "0044_field_dependencies"),
        ("core", "0012_add_trashed_indexes"),
    ]
    migrate_to = [("database", "0043_webhooks")]

    old_state = migrator.migrate(migrate_from)

    # The models used by the data_fixture below are not touched by this migration so
    # it is safe to use the latest version in the test
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

    FormulaField = old_state.apps.get_model("database", "FormulaField")
    ContentType = old_state.apps.get_model("contenttypes", "ContentType")
    content_type_id = ContentType.objects.get_for_model(FormulaField).id
    formula_field = FormulaField.objects.create(
        table_id=table.id,
        formula_type="text",
        formula=f"field('text')",
        internal_formula="something",
        requires_refresh_after_insert=False,
        content_type_id=content_type_id,
        version=2,
        order=0,
        name="a",
    )
    unknown_field = FormulaField.objects.create(
        table_id=table.id,
        formula_type="text",
        formula=f"field('unknown')",
        internal_formula="something",
        requires_refresh_after_insert=False,
        content_type_id=content_type_id,
        version=2,
        order=0,
        name="b",
    )

    new_state = migrator.migrate(migrate_to)
    NewFormulaField = new_state.apps.get_model("database", "FormulaField")

    new_formula_field = NewFormulaField.objects.get(id=formula_field.id)
    assert new_formula_field.formula == f"field('text')"
    new_unknown_field_by_id = NewFormulaField.objects.get(id=unknown_field.id)
    assert new_unknown_field_by_id.formula == "field('unknown')"
