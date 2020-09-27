import pytest

from baserow.core.exceptions import UserNotInGroupError
from baserow.contrib.database.views.handler import ViewHandler
from baserow.contrib.database.views.models import View, GridView, ViewFilter
from baserow.contrib.database.views.registries import (
    view_type_registry, view_filter_type_registry
)
from baserow.contrib.database.views.exceptions import (
    ViewTypeDoesNotExist, ViewDoesNotExist, UnrelatedFieldError,
    ViewFilterDoesNotExist, ViewFilterNotSupported, ViewFilterTypeNotAllowedForField,
    ViewFilterTypeDoesNotExist
)
from baserow.contrib.database.fields.models import Field
from baserow.contrib.database.fields.registries import field_type_registry
from baserow.contrib.database.fields.exceptions import FieldNotInTable


@pytest.mark.django_db
def test_get_view(data_fixture):
    user = data_fixture.create_user()
    user_2 = data_fixture.create_user()
    grid = data_fixture.create_grid_view(user=user)

    handler = ViewHandler()

    with pytest.raises(ViewDoesNotExist):
        handler.get_view(user=user, view_id=99999)

    with pytest.raises(UserNotInGroupError):
        handler.get_view(user=user_2, view_id=grid.id)

    view = handler.get_view(user=user, view_id=grid.id)

    assert view.id == grid.id
    assert view.name == grid.name
    assert view.filter_type == 'AND'
    assert isinstance(view, View)

    view = handler.get_view(user=user, view_id=grid.id, view_model=GridView)

    assert view.id == grid.id
    assert view.name == grid.name
    assert view.filter_type == 'AND'
    assert isinstance(view, GridView)

    # If the error is raised we know for sure that the query has resolved.
    with pytest.raises(AttributeError):
        handler.get_view(
            user=user, view_id=grid.id,
            base_queryset=View.objects.prefetch_related('UNKNOWN')
        )


@pytest.mark.django_db
def test_create_view(data_fixture):
    user = data_fixture.create_user()
    user_2 = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)

    handler = ViewHandler()
    handler.create_view(user=user, table=table, type_name='grid', name='Test grid')

    assert View.objects.all().count() == 1
    assert GridView.objects.all().count() == 1

    grid = GridView.objects.all().first()
    assert grid.name == 'Test grid'
    assert grid.order == 1
    assert grid.table == table
    assert grid.filter_type == 'AND'

    with pytest.raises(UserNotInGroupError):
        handler.create_view(user=user_2, table=table, type_name='grid', name='')

    with pytest.raises(ViewTypeDoesNotExist):
        handler.create_view(user=user, table=table, type_name='UNKNOWN', name='')


@pytest.mark.django_db
def test_update_view(data_fixture):
    user = data_fixture.create_user()
    user_2 = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    grid = data_fixture.create_grid_view(table=table)

    handler = ViewHandler()

    with pytest.raises(UserNotInGroupError):
        handler.update_view(user=user_2, view=grid, name='Test 1')

    with pytest.raises(ValueError):
        handler.update_view(user=user, view=object(), name='Test 1')

    handler.update_view(user=user, view=grid, name='Test 1')

    grid.refresh_from_db()
    assert grid.name == 'Test 1'

    handler.update_view(user=user, view=grid, filter_type='OR')

    grid.refresh_from_db()
    assert grid.filter_type == 'OR'


@pytest.mark.django_db
def test_delete_view(data_fixture):
    user = data_fixture.create_user()
    user_2 = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    grid = data_fixture.create_grid_view(table=table)

    handler = ViewHandler()

    with pytest.raises(UserNotInGroupError):
        handler.delete_view(user=user_2, view=grid)

    with pytest.raises(ValueError):
        handler.delete_view(user=user_2, view=object())

    assert View.objects.all().count() == 1
    handler.delete_view(user=user, view=grid)
    assert View.objects.all().count() == 0


@pytest.mark.django_db
def test_update_grid_view_field_options(data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    grid_view = data_fixture.create_grid_view(table=table)
    field_1 = data_fixture.create_text_field(table=table)
    field_2 = data_fixture.create_text_field(table=table)
    field_3 = data_fixture.create_text_field()

    with pytest.raises(ValueError):
        ViewHandler().update_grid_view_field_options(grid_view=grid_view, field_options={
            'strange_format': {'height': 150},
        })

    with pytest.raises(UnrelatedFieldError):
        ViewHandler().update_grid_view_field_options(grid_view=grid_view, field_options={
            99999: {'width': 150},
        })

    with pytest.raises(UnrelatedFieldError):
        ViewHandler().update_grid_view_field_options(grid_view=grid_view, field_options={
            field_3.id: {'width': 150},
        })

    ViewHandler().update_grid_view_field_options(grid_view=grid_view, field_options={
        str(field_1.id): {'width': 150},
        field_2.id: {'width': 250}
    })
    options_4 = grid_view.get_field_options()

    assert len(options_4) == 2
    assert options_4[0].width == 150
    assert options_4[0].field_id == field_1.id
    assert options_4[1].width == 250
    assert options_4[1].field_id == field_2.id

    field_4 = data_fixture.create_text_field(table=table)
    ViewHandler().update_grid_view_field_options(grid_view=grid_view, field_options={
        field_2.id: {'width': 300},
        field_4.id: {'width': 50}
    })
    options_4 = grid_view.get_field_options()
    assert len(options_4) == 3
    assert options_4[0].width == 150
    assert options_4[0].field_id == field_1.id
    assert options_4[1].width == 300
    assert options_4[1].field_id == field_2.id
    assert options_4[2].width == 50
    assert options_4[2].field_id == field_4.id


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


@pytest.mark.django_db
def test_get_filter(data_fixture):
    user = data_fixture.create_user()
    user_2 = data_fixture.create_user()
    equal_filter = data_fixture.create_view_filter(user=user)

    handler = ViewHandler()

    with pytest.raises(ViewFilterDoesNotExist):
        handler.get_filter(user=user, view_filter_id=99999)

    with pytest.raises(UserNotInGroupError):
        handler.get_filter(user=user_2, view_filter_id=equal_filter.id)

    filter = handler.get_filter(user=user, view_filter_id=equal_filter.id)

    assert filter.id == equal_filter.id
    assert filter.view_id == equal_filter.view_id
    assert filter.field_id == equal_filter.field_id
    assert filter.type == equal_filter.type
    assert filter.value == equal_filter.value


@pytest.mark.django_db
def test_create_filter(data_fixture):
    user = data_fixture.create_user()
    user_2 = data_fixture.create_user()
    grid_view = data_fixture.create_grid_view(user=user)
    text_field = data_fixture.create_text_field(table=grid_view.table)
    other_field = data_fixture.create_text_field()

    handler = ViewHandler()

    with pytest.raises(UserNotInGroupError):
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
def test_update_filter(data_fixture):
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

    with pytest.raises(UserNotInGroupError):
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
def test_delete_filter(data_fixture):
    user = data_fixture.create_user()
    filter_1 = data_fixture.create_view_filter(user=user)
    filter_2 = data_fixture.create_view_filter()

    assert ViewFilter.objects.all().count() == 2

    handler = ViewHandler()

    with pytest.raises(UserNotInGroupError):
        handler.delete_filter(user=user, view_filter=filter_2)

    handler.delete_filter(user=user, view_filter=filter_1)

    assert ViewFilter.objects.all().count() == 1
    assert ViewFilter.objects.filter(pk=filter_1.pk).count() == 0
