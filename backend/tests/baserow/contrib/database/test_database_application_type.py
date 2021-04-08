import pytest

from baserow.core.registries import application_type_registry


@pytest.mark.django_db
def test_import_export_database(data_fixture, user_tables_in_separate_db):
    database = data_fixture.create_database_application()
    table = data_fixture.create_database_table(database=database)
    text_field = data_fixture.create_text_field(table=table)
    view = data_fixture.create_grid_view(table=table)
    data_fixture.create_view_filter(view=view, field=text_field, value='Test')
    data_fixture.create_view_sort(view=view, field=text_field)
    model = table.get_model()
    row = model.objects.create(**{
        f'field_{text_field.id}': 'Test'
    })

    database_type = application_type_registry.get('database')
    serialized = database_type.export_serialized(database)
    imported_group = data_fixture.create_group()
    id_mapping = {}
    imported_database = database_type.import_serialized(
        imported_group,
        serialized,
        id_mapping
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
    assert imported_table.field_set.all().count() == 1
    assert imported_table.view_set.all().count() == 1

    imported_view = imported_table.view_set.all().first()
    assert imported_view.viewfilter_set.all().count() == 1
    assert imported_view.viewsort_set.all().count() == 1

    imported_model = imported_table.get_model()
    assert imported_model.objects.all().count() == 1
    imported_row = imported_model.objects.all().first()

    # Because the rows have unique id within the table, we expect the row id to be the
    # same.
    assert imported_row.id == row.id
    assert imported_row.order == row.order
    assert getattr(
        imported_row,
        f'field_{id_mapping["database_fields"][text_field.id]}'
    ) == (getattr(row, f'field_{text_field.id}'))

    # It must still be possible to create a new row in the imported table
    row_2 = imported_model.objects.create()
    assert row_2.id == 2
