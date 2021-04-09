import pytest
from unittest.mock import patch
from decimal import Decimal

from baserow.core.exceptions import UserNotInGroup
from baserow.contrib.database.views.handler import ViewHandler
from baserow.contrib.database.views.models import View, GridView, ViewFilter, ViewSort
from baserow.contrib.database.views.registries import (
    view_type_registry, view_filter_type_registry
)
from baserow.contrib.database.views.exceptions import (
    ViewTypeDoesNotExist, ViewDoesNotExist, UnrelatedFieldError,
    ViewFilterDoesNotExist, ViewFilterNotSupported, ViewFilterTypeNotAllowedForField,
    ViewFilterTypeDoesNotExist, ViewSortDoesNotExist, ViewSortNotSupported,
    ViewSortFieldAlreadyExist, ViewSortFieldNotSupported
)
from baserow.contrib.database.fields.models import Field
from baserow.contrib.database.fields.handler import FieldHandler
from baserow.contrib.database.fields.exceptions import FieldNotInTable


@pytest.mark.django_db
def test_get_view(data_fixture):
    user = data_fixture.create_user()
    data_fixture.create_user()
    grid = data_fixture.create_grid_view(user=user)

    handler = ViewHandler()

    with pytest.raises(ViewDoesNotExist):
        handler.get_view(view_id=99999)

    view = handler.get_view(view_id=grid.id)

    assert view.id == grid.id
    assert view.name == grid.name
    assert view.filter_type == 'AND'
    assert not view.filters_disabled
    assert isinstance(view, View)

    view = handler.get_view(view_id=grid.id, view_model=GridView)

    assert view.id == grid.id
    assert view.name == grid.name
    assert view.filter_type == 'AND'
    assert not view.filters_disabled
    assert isinstance(view, GridView)

    # If the error is raised we know for sure that the query has resolved.
    with pytest.raises(AttributeError):
        handler.get_view(
            view_id=grid.id,
            base_queryset=View.objects.prefetch_related('UNKNOWN')
        )


@pytest.mark.django_db
@patch('baserow.contrib.database.views.signals.view_created.send')
def test_create_view(send_mock, data_fixture):
    user = data_fixture.create_user()
    user_2 = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    table_2 = data_fixture.create_database_table(user=user)

    handler = ViewHandler()
    view = handler.create_view(user=user, table=table, type_name='grid',
                               name='Test grid')

    send_mock.assert_called_once()
    assert send_mock.call_args[1]['view'].id == view.id
    assert send_mock.call_args[1]['user'].id == user.id

    assert View.objects.all().count() == 1
    assert GridView.objects.all().count() == 1

    grid = GridView.objects.all().first()
    assert grid.name == 'Test grid'
    assert grid.order == 1
    assert grid.table == table
    assert grid.filter_type == 'AND'
    assert not grid.filters_disabled

    handler.create_view(user=user, table=table, type_name='grid',
                        name='Something else', filter_type='OR', filters_disabled=True)

    assert View.objects.all().count() == 2
    assert GridView.objects.all().count() == 2

    grid = GridView.objects.all().last()
    assert grid.name == 'Something else'
    assert grid.order == 2
    assert grid.table == table
    assert grid.filter_type == 'OR'
    assert grid.filters_disabled

    grid = handler.create_view(user=user, table=table_2, type_name='grid', name='Name',
                               filter_type='OR', filters_disabled=False)

    assert View.objects.all().count() == 3
    assert GridView.objects.all().count() == 3

    assert grid.name == 'Name'
    assert grid.order == 1
    assert grid.table == table_2
    assert grid.filter_type == 'OR'
    assert not grid.filters_disabled

    with pytest.raises(UserNotInGroup):
        handler.create_view(user=user_2, table=table, type_name='grid', name='')

    with pytest.raises(ViewTypeDoesNotExist):
        handler.create_view(user=user, table=table, type_name='UNKNOWN', name='')


@pytest.mark.django_db
@patch('baserow.contrib.database.views.signals.view_updated.send')
def test_update_view(send_mock, data_fixture):
    user = data_fixture.create_user()
    user_2 = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    grid = data_fixture.create_grid_view(table=table)

    handler = ViewHandler()

    with pytest.raises(UserNotInGroup):
        handler.update_view(user=user_2, view=grid, name='Test 1')

    with pytest.raises(ValueError):
        handler.update_view(user=user, view=object(), name='Test 1')

    view = handler.update_view(user=user, view=grid, name='Test 1')

    send_mock.assert_called_once()
    assert send_mock.call_args[1]['view'].id == view.id
    assert send_mock.call_args[1]['user'].id == user.id

    grid.refresh_from_db()
    assert grid.name == 'Test 1'
    assert grid.filter_type == 'AND'
    assert not grid.filters_disabled

    handler.update_view(user=user, view=grid, filter_type='OR', filters_disabled=True)

    grid.refresh_from_db()
    assert grid.filter_type == 'OR'
    assert grid.filters_disabled


@pytest.mark.django_db
@patch('baserow.contrib.database.views.signals.view_deleted.send')
def test_delete_view(send_mock, data_fixture):
    user = data_fixture.create_user()
    user_2 = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    grid = data_fixture.create_grid_view(table=table)

    handler = ViewHandler()

    with pytest.raises(UserNotInGroup):
        handler.delete_view(user=user_2, view=grid)

    with pytest.raises(ValueError):
        handler.delete_view(user=user_2, view=object())

    view_id = grid.id

    assert View.objects.all().count() == 1
    handler.delete_view(user=user, view=grid)
    assert View.objects.all().count() == 0

    send_mock.assert_called_once()
    assert send_mock.call_args[1]['view_id'] == view_id
    assert send_mock.call_args[1]['view'].id == view_id
    assert send_mock.call_args[1]['user'].id == user.id


@pytest.mark.django_db
@patch('baserow.contrib.database.views.signals.grid_view_field_options_updated.send')
def test_update_grid_view_field_options(send_mock, data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    grid_view = data_fixture.create_grid_view(table=table)
    field_1 = data_fixture.create_text_field(table=table)
    field_2 = data_fixture.create_text_field(table=table)
    field_3 = data_fixture.create_text_field()

    with pytest.raises(ValueError):
        ViewHandler().update_grid_view_field_options(
            user=user,
            grid_view=grid_view,
            field_options={
                'strange_format': {'height': 150},
            }
        )

    with pytest.raises(UserNotInGroup):
        ViewHandler().update_grid_view_field_options(
            user=data_fixture.create_user(),
            grid_view=grid_view,
            field_options={
                'strange_format': {'height': 150},
            }
        )

    with pytest.raises(UnrelatedFieldError):
        ViewHandler().update_grid_view_field_options(
            user=user,
            grid_view=grid_view,
            field_options={
                99999: {'width': 150},
            }
        )

    with pytest.raises(UnrelatedFieldError):
        ViewHandler().update_grid_view_field_options(
            user=user,
            grid_view=grid_view,
            field_options={
                field_3.id: {'width': 150},
            }
        )

    ViewHandler().update_grid_view_field_options(
        user=user,
        grid_view=grid_view,
        field_options={
            str(field_1.id): {'width': 150},
            field_2.id: {'width': 250}
        }
    )
    options_4 = grid_view.get_field_options()

    send_mock.assert_called_once()
    assert send_mock.call_args[1]['grid_view'].id == grid_view.id
    assert send_mock.call_args[1]['user'].id == user.id
    assert len(options_4) == 2
    assert options_4[0].width == 150
    assert options_4[0].field_id == field_1.id
    assert options_4[1].width == 250
    assert options_4[1].field_id == field_2.id

    field_4 = data_fixture.create_text_field(table=table)
    ViewHandler().update_grid_view_field_options(
        user=user,
        grid_view=grid_view,
        field_options={
            field_2.id: {'width': 300},
            field_4.id: {'width': 50}
        }
    )
    options_4 = grid_view.get_field_options()
    assert len(options_4) == 3
    assert options_4[0].width == 150
    assert options_4[0].field_id == field_1.id
    assert options_4[1].width == 300
    assert options_4[1].field_id == field_2.id
    assert options_4[2].width == 50
    assert options_4[2].field_id == field_4.id


@pytest.mark.django_db
def test_field_type_changed(data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    table_2 = data_fixture.create_database_table(user=user, database=table.database)
    text_field = data_fixture.create_text_field(table=table)
    grid_view = data_fixture.create_grid_view(table=table)
    data_fixture.create_view_filter(view=grid_view, field=text_field,
                                    type='contains', value='test')
    data_fixture.create_view_sort(view=grid_view, field=text_field, order='ASC')

    field_handler = FieldHandler()
    long_text_field = field_handler.update_field(user=user, field=text_field,
                                                 new_type_name='long_text')
    assert ViewFilter.objects.all().count() == 1
    assert ViewSort.objects.all().count() == 1

    field_handler.update_field(user=user, field=long_text_field,
                               new_type_name='boolean')
    assert ViewFilter.objects.all().count() == 0
    assert ViewSort.objects.all().count() == 1

    field_handler.update_field(user=user, field=long_text_field,
                               new_type_name='link_row', link_row_table=table_2)
    assert ViewFilter.objects.all().count() == 0
    assert ViewSort.objects.all().count() == 0


@pytest.mark.django_db
def test_apply_filters(data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    text_field = data_fixture.create_text_field(table=table)
    number_field = data_fixture.create_number_field(table=table)
    boolean_field = data_fixture.create_boolean_field(table=table)
    grid_view = data_fixture.create_grid_view(table=table)

    view_handler = ViewHandler()

    model = table.get_model()
    row_1 = model.objects.create(**{
        f'field_{text_field.id}': 'Value 1',
        f'field_{number_field.id}': 10,
        f'field_{boolean_field.id}': True
    })
    row_2 = model.objects.create(**{
        f'field_{text_field.id}': 'Entry 2',
        f'field_{number_field.id}': 20,
        f'field_{boolean_field.id}': False
    })
    row_3 = model.objects.create(**{
        f'field_{text_field.id}': 'Item 3',
        f'field_{number_field.id}': 30,
        f'field_{boolean_field.id}': True
    })
    row_4 = model.objects.create(**{
        f'field_{text_field.id}': '',
        f'field_{number_field.id}': None,
        f'field_{boolean_field.id}': False
    })

    filter_1 = data_fixture.create_view_filter(view=grid_view, field=text_field,
                                               type='equal', value='Value 1')

    # Should raise a value error if the modal doesn't have the _field_objects property.
    with pytest.raises(ValueError):
        view_handler.apply_filters(grid_view, GridView.objects.all())

    # Should raise a value error if the field is not included in the model.
    with pytest.raises(ValueError):
        view_handler.apply_filters(
            grid_view,
            table.get_model(field_ids=[]).objects.all()
        )

    rows = view_handler.apply_filters(grid_view, model.objects.all())
    assert len(rows) == 1
    assert rows[0].id == row_1.id

    filter_2 = data_fixture.create_view_filter(view=grid_view, field=number_field,
                                               type='equal', value='20')
    filter_1.value = 'Entry 2'
    filter_1.save()
    rows = view_handler.apply_filters(grid_view, model.objects.all())
    assert len(rows) == 1
    assert rows[0].id == row_2.id

    filter_1.value = 'Item 3'
    filter_1.type = 'equal'
    filter_1.save()
    filter_2.value = '20'
    filter_2.type = 'not_equal'
    filter_2.save()
    rows = view_handler.apply_filters(grid_view, model.objects.all())
    assert len(rows) == 1
    assert rows[0].id == row_3.id

    grid_view.filter_type = 'OR'
    filter_1.value = 'Value 1'
    filter_1.type = 'equal'
    filter_1.save()
    filter_2.field = text_field
    filter_2.value = 'Entry 2'
    filter_2.type = 'equal'
    filter_2.save()
    rows = view_handler.apply_filters(grid_view, model.objects.all())
    assert len(rows) == 2
    assert rows[0].id == row_1.id
    assert rows[1].id == row_2.id

    filter_2.delete()

    grid_view.filter_type = 'AND'
    filter_1.value = ''
    filter_1.type = 'empty'
    filter_1.save()
    rows = view_handler.apply_filters(grid_view, model.objects.all())
    assert len(rows) == 1
    assert rows[0].id == row_4.id

    grid_view.filter_type = 'AND'
    filter_1.value = ''
    filter_1.type = 'not_empty'
    filter_1.save()
    rows = view_handler.apply_filters(grid_view, model.objects.all())
    assert len(rows) == 3
    assert rows[0].id == row_1.id
    assert rows[1].id == row_2.id
    assert rows[2].id == row_3.id

    grid_view.filter_type = 'AND'
    filter_1.value = '1'
    filter_1.type = 'equal'
    filter_1.field = boolean_field
    filter_1.save()
    rows = view_handler.apply_filters(grid_view, model.objects.all())
    assert len(rows) == 2
    assert rows[0].id == row_1.id
    assert rows[1].id == row_3.id

    grid_view.filter_type = 'AND'
    filter_1.value = '1'
    filter_1.type = 'not_equal'
    filter_1.field = boolean_field
    filter_1.save()
    rows = view_handler.apply_filters(grid_view, model.objects.all())
    assert len(rows) == 2
    assert rows[0].id == row_2.id
    assert rows[1].id == row_4.id

    grid_view.filter_type = 'AND'
    filter_1.value = 'False'
    filter_1.type = 'equal'
    filter_1.field = boolean_field
    filter_1.save()
    rows = view_handler.apply_filters(grid_view, model.objects.all())
    assert len(rows) == 2
    assert rows[0].id == row_2.id
    assert rows[1].id == row_4.id

    grid_view.filters_disabled = True
    grid_view.save()
    rows = view_handler.apply_filters(grid_view, model.objects.all())
    assert rows[0].id == row_1.id
    assert rows[1].id == row_2.id
    assert rows[2].id == row_3.id
    assert rows[3].id == row_4.id


@pytest.mark.django_db
def test_get_filter(data_fixture):
    user = data_fixture.create_user()
    user_2 = data_fixture.create_user()
    equal_filter = data_fixture.create_view_filter(user=user)

    handler = ViewHandler()

    with pytest.raises(ViewFilterDoesNotExist):
        handler.get_filter(user=user, view_filter_id=99999)

    with pytest.raises(UserNotInGroup):
        handler.get_filter(user=user_2, view_filter_id=equal_filter.id)

    with pytest.raises(AttributeError):
        handler.get_filter(
            user=user,
            view_filter_id=equal_filter.id,
            base_queryset=ViewFilter.objects.prefetch_related('UNKNOWN')
        )

    filter = handler.get_filter(user=user, view_filter_id=equal_filter.id)

    assert filter.id == equal_filter.id
    assert filter.view_id == equal_filter.view_id
    assert filter.field_id == equal_filter.field_id
    assert filter.type == equal_filter.type
    assert filter.value == equal_filter.value


@pytest.mark.django_db
@patch('baserow.contrib.database.views.signals.view_filter_created.send')
def test_create_filter(send_mock, data_fixture):
    user = data_fixture.create_user()
    user_2 = data_fixture.create_user()
    grid_view = data_fixture.create_grid_view(user=user)
    text_field = data_fixture.create_text_field(table=grid_view.table)
    other_field = data_fixture.create_text_field()

    handler = ViewHandler()

    with pytest.raises(UserNotInGroup):
        handler.create_filter(user=user_2, view=grid_view, field=text_field,
                              type_name='equal', value='test')

    grid_view_type = view_type_registry.get('grid')
    grid_view_type.can_filter = False
    with pytest.raises(ViewFilterNotSupported):
        handler.create_filter(user=user, view=grid_view, field=text_field,
                              type_name='equal', value='test')
    grid_view_type.can_filter = True

    with pytest.raises(ViewFilterTypeDoesNotExist):
        handler.create_filter(user=user, view=grid_view, field=text_field,
                              type_name='NOT_EXISTS', value='test')

    equal_filter_type = view_filter_type_registry.get('equal')
    allowed = equal_filter_type.compatible_field_types
    equal_filter_type.compatible_field_types = []
    with pytest.raises(ViewFilterTypeNotAllowedForField):
        handler.create_filter(user=user, view=grid_view, field=text_field,
                              type_name='equal', value='test')
    equal_filter_type.compatible_field_types = allowed

    with pytest.raises(FieldNotInTable):
        handler.create_filter(user=user, view=grid_view, field=other_field,
                              type_name='equal', value='test')

    view_filter = handler.create_filter(user=user, view=grid_view, field=text_field,
                                        type_name='equal', value='test')

    send_mock.assert_called_once()
    assert send_mock.call_args[1]['view_filter'].id == view_filter.id
    assert send_mock.call_args[1]['user'].id == user.id

    assert ViewFilter.objects.all().count() == 1
    first = ViewFilter.objects.all().first()

    assert view_filter.id == first.id
    assert view_filter.view_id == grid_view.id
    assert view_filter.field_id == text_field.id
    assert view_filter.type == 'equal'
    assert view_filter.value == 'test'

    tmp_field = Field.objects.get(pk=text_field.id)
    view_filter_2 = handler.create_filter(user=user, view=grid_view, field=tmp_field,
                                          type_name='equal', value='test')
    assert view_filter_2.view_id == grid_view.id
    assert view_filter_2.field_id == text_field.id
    assert view_filter_2.type == 'equal'
    assert view_filter_2.value == 'test'


@pytest.mark.django_db
@patch('baserow.contrib.database.views.signals.view_filter_updated.send')
def test_update_filter(send_mock, data_fixture):
    user = data_fixture.create_user()
    user_2 = data_fixture.create_user()
    grid_view = data_fixture.create_grid_view(user=user)
    text_field = data_fixture.create_text_field(table=grid_view.table)
    long_text_field = data_fixture.create_long_text_field(table=grid_view.table)
    other_field = data_fixture.create_text_field()
    equal_filter = data_fixture.create_view_filter(
        view=grid_view,
        field=long_text_field,
        type='equal',
        value='test1'
    )

    handler = ViewHandler()

    with pytest.raises(UserNotInGroup):
        handler.update_filter(user=user_2, view_filter=equal_filter)

    with pytest.raises(ViewFilterTypeDoesNotExist):
        handler.update_filter(user=user, view_filter=equal_filter,
                              type_name='NOT_EXISTS')

    equal_filter_type = view_filter_type_registry.get('equal')
    allowed = equal_filter_type.compatible_field_types
    equal_filter_type.compatible_field_types = []
    with pytest.raises(ViewFilterTypeNotAllowedForField):
        handler.update_filter(user=user, view_filter=equal_filter, field=text_field)
    equal_filter_type.compatible_field_types = allowed

    with pytest.raises(FieldNotInTable):
        handler.update_filter(user=user, view_filter=equal_filter, field=other_field)

    updated_filter = handler.update_filter(user=user, view_filter=equal_filter,
                                           value='test2')
    send_mock.assert_called_once()
    assert send_mock.call_args[1]['view_filter'].id == updated_filter.id
    assert send_mock.call_args[1]['user'].id == user.id
    assert updated_filter.value == 'test2'
    assert updated_filter.field_id == long_text_field.id
    assert updated_filter.type == 'equal'
    assert updated_filter.view_id == grid_view.id

    updated_filter = handler.update_filter(user=user, view_filter=equal_filter,
                                           value='test3', field=text_field,
                                           type_name='not_equal')
    assert updated_filter.value == 'test3'
    assert updated_filter.field_id == text_field.id
    assert updated_filter.type == 'not_equal'
    assert updated_filter.view_id == grid_view.id


@pytest.mark.django_db
@patch('baserow.contrib.database.views.signals.view_filter_deleted.send')
def test_delete_filter(send_mock, data_fixture):
    user = data_fixture.create_user()
    filter_1 = data_fixture.create_view_filter(user=user)
    filter_2 = data_fixture.create_view_filter()

    assert ViewFilter.objects.all().count() == 2

    handler = ViewHandler()

    with pytest.raises(UserNotInGroup):
        handler.delete_filter(user=user, view_filter=filter_2)

    filter_1_id = filter_1.id
    handler.delete_filter(user=user, view_filter=filter_1)

    send_mock.assert_called_once()
    assert send_mock.call_args[1]['view_filter_id'] == filter_1_id
    assert send_mock.call_args[1]['view_filter']
    assert send_mock.call_args[1]['user'].id == user.id
    assert ViewFilter.objects.all().count() == 1
    assert ViewFilter.objects.filter(pk=filter_1.pk).count() == 0


@pytest.mark.django_db
def test_apply_sortings(data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    text_field = data_fixture.create_text_field(table=table)
    number_field = data_fixture.create_number_field(table=table)
    boolean_field = data_fixture.create_boolean_field(table=table)
    grid_view = data_fixture.create_grid_view(table=table)

    view_handler = ViewHandler()

    model = table.get_model()
    row_1 = model.objects.create(**{
        f'field_{text_field.id}': 'Aaa',
        f'field_{number_field.id}': 30,
        f'field_{boolean_field.id}': True
    })
    row_2 = model.objects.create(**{
        f'field_{text_field.id}': 'Aaa',
        f'field_{number_field.id}': 20,
        f'field_{boolean_field.id}': True
    })
    row_3 = model.objects.create(**{
        f'field_{text_field.id}': 'Aaa',
        f'field_{number_field.id}': 10,
        f'field_{boolean_field.id}': False
    })
    row_4 = model.objects.create(**{
        f'field_{text_field.id}': 'Bbbb',
        f'field_{number_field.id}': 60,
        f'field_{boolean_field.id}': False
    })
    row_5 = model.objects.create(**{
        f'field_{text_field.id}': 'Cccc',
        f'field_{number_field.id}': 50,
        f'field_{boolean_field.id}': False
    })
    row_6 = model.objects.create(**{
        f'field_{text_field.id}': 'Dddd',
        f'field_{number_field.id}': 40,
        f'field_{boolean_field.id}': True
    })

    # Without any sortings.
    rows = view_handler.apply_sorting(grid_view, model.objects.all())
    row_ids = [row.id for row in rows]
    assert row_ids == [row_1.id, row_2.id, row_3.id, row_4.id, row_5.id, row_6.id]

    sort = data_fixture.create_view_sort(view=grid_view, field=text_field,
                                         order='ASC')

    # Should raise a value error if the modal doesn't have the _field_objects property.
    with pytest.raises(ValueError):
        view_handler.apply_sorting(grid_view, GridView.objects.all())

    # Should raise a value error if the field is not included in the model.
    with pytest.raises(ValueError):
        view_handler.apply_sorting(
            grid_view,
            table.get_model(field_ids=[]).objects.all()
        )

    rows = view_handler.apply_sorting(grid_view, model.objects.all())
    row_ids = [row.id for row in rows]
    assert row_ids == [row_1.id, row_2.id, row_3.id, row_4.id, row_5.id, row_6.id]

    sort.order = 'DESC'
    sort.save()
    rows = view_handler.apply_sorting(grid_view, model.objects.all())
    row_ids = [row.id for row in rows]
    assert row_ids == [row_6.id, row_5.id, row_4.id, row_1.id, row_2.id, row_3.id]

    sort.order = 'ASC'
    sort.field_id = number_field.id
    sort.save()
    rows = view_handler.apply_sorting(grid_view, model.objects.all())
    row_ids = [row.id for row in rows]
    assert row_ids == [row_3.id, row_2.id, row_1.id, row_6.id, row_5.id, row_4.id]

    sort.field_id = boolean_field.id
    sort.save()
    rows = view_handler.apply_sorting(grid_view, model.objects.all())
    row_ids = [row.id for row in rows]
    assert row_ids == [row_3.id, row_4.id, row_5.id, row_1.id, row_2.id, row_6.id]

    sort.field_id = text_field.id
    sort.save()
    sort_2 = data_fixture.create_view_sort(view=grid_view, field=number_field,
                                           order='ASC')
    rows = view_handler.apply_sorting(grid_view, model.objects.all())
    row_ids = [row.id for row in rows]
    assert row_ids == [row_3.id, row_2.id, row_1.id, row_4.id, row_5.id, row_6.id]

    sort.field_id = text_field.id
    sort.save()
    sort_2.field_id = boolean_field
    sort_2.order = 'DESC'
    sort_2.save()
    rows = view_handler.apply_sorting(grid_view, model.objects.all())
    row_ids = [row.id for row in rows]
    assert row_ids == [row_1.id, row_2.id, row_3.id, row_4.id, row_5.id, row_6.id]

    sort.field_id = text_field.id
    sort.order = 'DESC'
    sort.save()
    sort_2.field_id = boolean_field
    sort_2.order = 'ASC'
    sort_2.save()
    rows = view_handler.apply_sorting(grid_view, model.objects.all())
    row_ids = [row.id for row in rows]
    assert row_ids == [row_6.id, row_5.id, row_4.id, row_3.id, row_1.id, row_2.id]

    sort.field_id = number_field.id
    sort.save()
    rows = view_handler.apply_sorting(grid_view, model.objects.all())
    row_ids = [row.id for row in rows]
    assert row_ids == [row_4.id, row_5.id, row_6.id, row_1.id, row_2.id, row_3.id]

    row_7 = model.objects.create(**{
        f'field_{text_field.id}': 'Aaa',
        f'field_{number_field.id}': 30,
        f'field_{boolean_field.id}': True,
        'order': Decimal('0.1')
    })

    sort.delete()
    sort_2.delete()
    rows = view_handler.apply_sorting(grid_view, model.objects.all())
    row_ids = [row.id for row in rows]
    assert row_ids == [row_7.id, row_1.id, row_2.id, row_3.id, row_4.id, row_5.id,
                       row_6.id]


@pytest.mark.django_db
def test_get_sort(data_fixture):
    user = data_fixture.create_user()
    user_2 = data_fixture.create_user()
    equal_sort = data_fixture.create_view_sort(user=user)

    handler = ViewHandler()

    with pytest.raises(ViewSortDoesNotExist):
        handler.get_sort(user=user, view_sort_id=99999)

    with pytest.raises(UserNotInGroup):
        handler.get_sort(user=user_2, view_sort_id=equal_sort.id)

    with pytest.raises(AttributeError):
        handler.get_sort(
            user=user,
            view_sort_id=equal_sort.id,
            base_queryset=ViewSort.objects.prefetch_related('UNKNOWN')
        )

    sort = handler.get_sort(user=user, view_sort_id=equal_sort.id)

    assert sort.id == equal_sort.id
    assert sort.view_id == equal_sort.view_id
    assert sort.field_id == equal_sort.field_id
    assert sort.order == equal_sort.order


@pytest.mark.django_db
@patch('baserow.contrib.database.views.signals.view_sort_created.send')
def test_create_sort(send_mock, data_fixture):
    user = data_fixture.create_user()
    user_2 = data_fixture.create_user()
    grid_view = data_fixture.create_grid_view(user=user)
    text_field = data_fixture.create_text_field(table=grid_view.table)
    text_field_2 = data_fixture.create_text_field(table=grid_view.table)
    link_row_field = data_fixture.create_link_row_field(table=grid_view.table)
    other_field = data_fixture.create_text_field()

    handler = ViewHandler()

    with pytest.raises(UserNotInGroup):
        handler.create_sort(user=user_2, view=grid_view, field=text_field,
                            order='ASC')

    grid_view_type = view_type_registry.get('grid')
    grid_view_type.can_sort = False
    with pytest.raises(ViewSortNotSupported):
        handler.create_sort(user=user, view=grid_view, field=text_field,
                            order='ASC')
    grid_view_type.can_sort = True

    with pytest.raises(ViewSortFieldNotSupported):
        handler.create_sort(user=user, view=grid_view, field=link_row_field,
                            order='ASC')

    with pytest.raises(FieldNotInTable):
        handler.create_sort(user=user, view=grid_view, field=other_field,
                            order='ASC')

    view_sort = handler.create_sort(user=user, view=grid_view, field=text_field,
                                    order='ASC')

    send_mock.assert_called_once()
    assert send_mock.call_args[1]['view_sort'].id == view_sort.id
    assert send_mock.call_args[1]['user'].id == user.id

    assert ViewSort.objects.all().count() == 1
    first = ViewSort.objects.all().first()

    assert view_sort.id == first.id
    assert view_sort.view_id == grid_view.id
    assert view_sort.field_id == text_field.id
    assert view_sort.order == 'ASC'

    with pytest.raises(ViewSortFieldAlreadyExist):
        handler.create_sort(user=user, view=grid_view, field=text_field, order='ASC')

    view_sort_2 = handler.create_sort(user=user, view=grid_view, field=text_field_2,
                                      order='DESC')
    assert view_sort_2.view_id == grid_view.id
    assert view_sort_2.field_id == text_field_2.id
    assert view_sort_2.order == 'DESC'
    assert ViewSort.objects.all().count() == 2


@pytest.mark.django_db
@patch('baserow.contrib.database.views.signals.view_sort_updated.send')
def test_update_sort(send_mock, data_fixture):
    user = data_fixture.create_user()
    user_2 = data_fixture.create_user()
    grid_view = data_fixture.create_grid_view(user=user)
    text_field = data_fixture.create_text_field(table=grid_view.table)
    long_text_field = data_fixture.create_long_text_field(table=grid_view.table)
    link_row_field = data_fixture.create_link_row_field(table=grid_view.table)
    other_field = data_fixture.create_text_field()
    view_sort = data_fixture.create_view_sort(
        view=grid_view,
        field=long_text_field,
        order='ASC',
    )

    handler = ViewHandler()

    with pytest.raises(UserNotInGroup):
        handler.update_sort(user=user_2, view_sort=view_sort)

    with pytest.raises(ViewSortFieldNotSupported):
        handler.update_sort(user=user, view_sort=view_sort, field=link_row_field)

    with pytest.raises(FieldNotInTable):
        handler.update_sort(user=user, view_sort=view_sort, field=other_field)

    updated_sort = handler.update_sort(user=user, view_sort=view_sort,
                                       order='DESC')
    send_mock.assert_called_once()
    assert send_mock.call_args[1]['view_sort'].id == updated_sort.id
    assert send_mock.call_args[1]['user'].id == user.id
    assert updated_sort.order == 'DESC'
    assert updated_sort.field_id == long_text_field.id
    assert updated_sort.view_id == grid_view.id

    updated_sort = handler.update_sort(user=user, view_sort=updated_sort,
                                       order='ASC', field=text_field)
    assert updated_sort.order == 'ASC'
    assert updated_sort.field_id == text_field.id
    assert updated_sort.view_id == grid_view.id

    data_fixture.create_view_sort(view=grid_view, field=long_text_field)

    with pytest.raises(ViewSortFieldAlreadyExist):
        handler.update_sort(user=user, view_sort=view_sort, order='ASC',
                            field=long_text_field)


@pytest.mark.django_db
@patch('baserow.contrib.database.views.signals.view_sort_deleted.send')
def test_delete_sort(send_mock, data_fixture):
    user = data_fixture.create_user()
    sort_1 = data_fixture.create_view_sort(user=user)
    sort_2 = data_fixture.create_view_sort()

    assert ViewSort.objects.all().count() == 2

    handler = ViewHandler()

    with pytest.raises(UserNotInGroup):
        handler.delete_sort(user=user, view_sort=sort_2)

    sort_1_id = sort_1.id
    handler.delete_sort(user=user, view_sort=sort_1)

    send_mock.assert_called_once()
    assert send_mock.call_args[1]['view_sort_id'] == sort_1_id
    assert send_mock.call_args[1]['view_sort']
    assert send_mock.call_args[1]['user'].id == user.id

    assert ViewSort.objects.all().count() == 1
    assert ViewSort.objects.filter(pk=sort_1.pk).count() == 0
