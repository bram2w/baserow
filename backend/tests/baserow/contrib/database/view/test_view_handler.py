import pytest

from baserow.core.exceptions import UserNotInGroupError
from baserow.contrib.database.views.handler import ViewHandler
from baserow.contrib.database.views.models import View, GridView
from baserow.contrib.database.views.exceptions import (
    ViewTypeDoesNotExist, ViewDoesNotExist, UnrelatedFieldError
)


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
    assert isinstance(view, View)

    view = handler.get_view(user=user, view_id=grid.id, view_model=GridView)

    assert view.id == grid.id
    assert view.name == grid.name
    assert isinstance(view, GridView)


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
