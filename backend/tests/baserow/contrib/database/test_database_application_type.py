import pytest

from pytz import UTC
from datetime import datetime
from freezegun import freeze_time

from baserow.contrib.database.fields.models import FormulaField, TextField
from baserow.core.registries import application_type_registry


@pytest.mark.django_db
def test_import_export_database(data_fixture):
    database = data_fixture.create_database_application()
    table = data_fixture.create_database_table(database=database)
    text_field = data_fixture.create_text_field(table=table, name="text")
    formula_field = data_fixture.create_formula_field(
        table=table,
        name="formula",
        formula=f"field('{text_field.name}')",
        formula_type="text",
    )
    view = data_fixture.create_grid_view(table=table)
    data_fixture.create_view_filter(view=view, field=text_field, value="Test")
    data_fixture.create_view_sort(view=view, field=text_field)
    model = table.get_model()
    row = model.objects.create(**{f"field_{text_field.id}": "Test"})
    model.objects.create(**{f"field_{text_field.id}": "Test 2"})
    model.objects.filter(id=row.id).update(
        created_on=datetime(2021, 1, 1, 12, 30, tzinfo=UTC),
        updated_on=datetime(2021, 1, 2, 13, 30, tzinfo=UTC),
    )
    row.refresh_from_db()

    database_type = application_type_registry.get("database")
    serialized = database_type.export_serialized(database, None, None)

    # Delete the updated on, because the import should also be compatible with
    # without these values present.
    del serialized["tables"][0]["rows"][1]["created_on"]
    del serialized["tables"][0]["rows"][1]["updated_on"]

    imported_group = data_fixture.create_group()
    id_mapping = {}

    with freeze_time("2022-01-01 12:00"):
        imported_database = database_type.import_serialized(
            imported_group, serialized, id_mapping, None, None
        )

    assert imported_database.id != database.id
    assert imported_database.group_id == imported_group.id
    assert imported_database.name == database.name
    assert imported_database.order == database.order
    assert imported_database.table_set.all().count() == 1

    imported_table = imported_database.table_set.all().first()
    assert imported_table.id != table.id
    assert imported_table.name == table.name
    assert imported_table.order == table.order
    assert imported_table.field_set.all().count() == 2
    assert imported_table.view_set.all().count() == 1

    imported_view = imported_table.view_set.all().first()
    assert imported_view.viewfilter_set.all().count() == 1
    assert imported_view.viewsort_set.all().count() == 1

    imported_model = imported_table.get_model()
    assert imported_model.objects.all().count() == 2
    imported_row = imported_model.objects.all().first()
    imported_row_2 = imported_model.objects.all().last()

    imported_text_field = TextField.objects.get(table=imported_table)
    imported_formula_field = FormulaField.objects.get(table=imported_table)
    assert imported_formula_field.formula == f"field('{imported_text_field.name}')"

    # Because the rows have unique id within the table, we expect the row id to be the
    # same.
    assert imported_row.id == row.id
    assert imported_row.order == row.order
    assert imported_row.created_on == datetime(2021, 1, 1, 12, 30, tzinfo=UTC)
    assert imported_row.updated_on == datetime(2021, 1, 2, 13, 30, tzinfo=UTC)
    assert getattr(
        imported_row, f'field_{id_mapping["database_fields"][text_field.id]}'
    ) == (getattr(row, f"field_{text_field.id}"))
    assert (
        imported_formula_field.internal_formula == f"error_to_null(field('"
        f"{imported_text_field.db_column}'))"
    )
    assert imported_formula_field.formula_type == "text"
    assert getattr(
        imported_row, f'field_{id_mapping["database_fields"][formula_field.id]}'
    ) == (getattr(row, f"field_{formula_field.id}"))

    # Because the created on and updated on were not provided, we expect these values
    # to be equal to "now", which was frozen by freezegun during the import.
    assert imported_row_2.created_on == datetime(2022, 1, 1, 12, 0, tzinfo=UTC)
    assert imported_row_2.updated_on == datetime(2022, 1, 1, 12, 0, tzinfo=UTC)

    # It must still be possible to create a new row in the imported table
    row_3 = imported_model.objects.create()
    assert row_3.id == 3
