import pytest

from django.db import connection
from django.db.migrations.executor import MigrationExecutor


@pytest.mark.django_db
def test_forwards_migration(data_fixture, transactional_db, django_assert_num_queries):
    migrate_from = [("database", "0057_fix_invalid_type_filters_and_sorts")]
    migrate_to = [("database", "0058_fix_hanging_formula_field_metadata")]

    old_state = migrate(migrate_from)

    # The models used by the data_fixture below are not touched by this migration so
    # it is safe to use the latest version in the test.
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    FormulaField = old_state.apps.get_model("database", "FormulaField")
    TextField = old_state.apps.get_model("database", "TextField")
    LookupField = old_state.apps.get_model("database", "LookupField")
    ContentType = old_state.apps.get_model("contenttypes", "ContentType")
    text_field_content_type_id = ContentType.objects.get_for_model(TextField).id
    lookup_field_content_type_id = ContentType.objects.get_for_model(LookupField).id
    formula_field_content_type_id = ContentType.objects.get_for_model(FormulaField).id

    lookup_field = LookupField.objects.create(
        table_id=table.id,
        order=0,
        name="lookup",
        content_type_id=lookup_field_content_type_id,
        formula_type="invalid",
        formula=f"lookup('broken', 'broken')",
        requires_refresh_after_insert=False,
        version=2,
    )
    field_ptr_id = lookup_field.formulafield_ptr.field_ptr_id
    lookup_field.delete(keep_parents=True)
    text_field_with_hanging_formula_metadata = TextField.objects.create(
        field_ptr_id=field_ptr_id,
        table_id=table.id,
        content_type_id=text_field_content_type_id,
        order=0,
        name="text",
        created_on=lookup_field.created_on,
    )
    normal_text_field = TextField.objects.create(
        table_id=table.id,
        content_type_id=text_field_content_type_id,
        order=0,
        name="text2",
    )
    normal_lookup_field = LookupField.objects.create(
        table_id=table.id,
        order=0,
        name="normal_lookup",
        content_type_id=lookup_field_content_type_id,
        formula_type="invalid",
        formula=f"lookup('broken', 'broken')",
        requires_refresh_after_insert=False,
        version=2,
    )
    normal_formula_field = FormulaField.objects.create(
        table_id=table.id,
        order=0,
        name="normal_lookup",
        content_type_id=formula_field_content_type_id,
        formula_type="invalid",
        formula=f"lookup('broken', 'broken')",
        requires_refresh_after_insert=False,
        version=2,
    )

    assert TextField.objects.filter(
        id=text_field_with_hanging_formula_metadata.id
    ).exists()
    assert FormulaField.objects.filter(
        id=text_field_with_hanging_formula_metadata.id
    ).exists()

    new_state = migrate(migrate_to)

    NewLookupField = new_state.apps.get_model("database", "LookupField")
    NewFormulaField = new_state.apps.get_model("database", "FormulaField")
    NewTextField = new_state.apps.get_model("database", "TextField")

    # The text field with hanging meta data should no longer have the hanging
    # formula metadata
    assert NewTextField.objects.filter(
        id=text_field_with_hanging_formula_metadata.id
    ).exists()
    assert not NewFormulaField.objects.filter(
        id=text_field_with_hanging_formula_metadata.id
    ).exists()

    # A normal text field shouldn't have been changed
    assert NewTextField.objects.filter(id=normal_text_field.id).exists()

    # A lookup field should still have a FormulaField row
    assert NewLookupField.objects.filter(id=normal_lookup_field.id).exists()
    assert NewFormulaField.objects.filter(id=normal_lookup_field.id).exists()

    # A normal formula field should still just be a formula field row on its own
    assert NewFormulaField.objects.filter(id=normal_formula_field.id).exists()
    assert not NewLookupField.objects.filter(id=normal_formula_field.id).exists()


def migrate(target):
    executor = MigrationExecutor(connection)
    executor.loader.build_graph()  # reload.
    executor.migrate(target)
    new_state = executor.loader.project_state(target)
    return new_state
