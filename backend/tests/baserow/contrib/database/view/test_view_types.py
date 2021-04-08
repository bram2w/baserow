import pytest

from baserow.contrib.database.views.registries import view_type_registry


@pytest.mark.django_db
def test_import_export_grid_view(data_fixture):
    grid_view = data_fixture.create_grid_view(
        name='Test',
        order=1,
        filter_type='AND',
        filters_disabled=False
    )
    field = data_fixture.create_text_field(table=grid_view.table)
    imported_field = data_fixture.create_text_field(table=grid_view.table)
    field_option = data_fixture.create_grid_view_field_option(
        grid_view=grid_view,
        field=field
    )
    view_filter = data_fixture.create_view_filter(
        view=grid_view,
        field=field,
        value='test',
        type='equal'
    )
    view_sort = data_fixture.create_view_sort(
        view=grid_view,
        field=field,
        order='ASC'
    )

    id_mapping = {'database_fields': {field.id: imported_field.id}}

    grid_view_type = view_type_registry.get('grid')
    serialized = grid_view_type.export_serialized(grid_view)
    imported_grid_view = grid_view_type.import_serialized(
        grid_view.table,
        serialized,
        id_mapping
    )

    assert grid_view.id != imported_grid_view.id
    assert grid_view.name == imported_grid_view.name
    assert grid_view.order == imported_grid_view.order
    assert grid_view.filter_type == imported_grid_view.filter_type
    assert grid_view.filters_disabled == imported_grid_view.filters_disabled
    assert imported_grid_view.viewfilter_set.all().count() == 1
    assert imported_grid_view.viewsort_set.all().count() == 1

    imported_view_filter = imported_grid_view.viewfilter_set.all().first()
    assert view_filter.id != imported_view_filter.id
    assert imported_field.id == imported_view_filter.field_id
    assert view_filter.value == imported_view_filter.value
    assert view_filter.type == imported_view_filter.type

    imported_view_sort = imported_grid_view.viewsort_set.all().first()
    assert view_sort.id != imported_view_sort.id
    assert imported_field.id == imported_view_sort.field_id
    assert view_sort.order == imported_view_sort.order

    imported_field_options = imported_grid_view.get_field_options()
    imported_field_option = imported_field_options[0]
    assert field_option.id != imported_field_option.id
    assert imported_field.id == imported_field_option.field_id
    assert field_option.width == imported_field_option.width
    assert field_option.hidden == imported_field_option.hidden
    assert field_option.order == imported_field_option.order
