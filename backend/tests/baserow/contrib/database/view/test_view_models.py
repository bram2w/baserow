import pytest


@pytest.mark.django_db
def test_grid_view_get_field_options(data_fixture):
    table = data_fixture.create_database_table()
    table_2 = data_fixture.create_database_table()
    data_fixture.create_text_field(table=table_2)
    field_1 = data_fixture.create_text_field(table=table)
    field_2 = data_fixture.create_text_field(table=table)
    grid_view = data_fixture.create_grid_view(table=table)

    field_options = grid_view.get_field_options()
    assert len(field_options) == 2
    assert field_options[0].field_id == field_1.id
    assert field_options[0].width == 200
    assert field_options[0].order == 32767
    assert field_options[1].field_id == field_2.id
    assert field_options[1].width == 200
    assert field_options[1].order == 32767

    field_3 = data_fixture.create_text_field(table=table)

    field_options = grid_view.get_field_options()
    assert len(field_options) == 2

    field_options = grid_view.get_field_options(create_if_not_exists=True)
    assert len(field_options) == 3
    assert field_options[0].field_id == field_1.id
    assert field_options[1].field_id == field_2.id
    assert field_options[2].field_id == field_3.id

    field_options = grid_view.get_field_options(create_if_not_exists=False)
    assert len(field_options) == 3
    assert field_options[0].field_id == field_1.id
    assert field_options[1].field_id == field_2.id
    assert field_options[2].field_id == field_3.id
