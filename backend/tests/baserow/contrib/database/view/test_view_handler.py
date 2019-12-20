import pytest

from baserow.core.exceptions import UserNotInGroupError
from baserow.contrib.database.views.handler import ViewHandler
from baserow.contrib.database.views.models import View, GridView
from baserow.contrib.database.views.exceptions import ViewTypeDoesNotExist


@pytest.mark.django_db
def test_create_database_application(data_fixture):
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
def test_update_database_application(data_fixture):
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
def test_delete_database_application(data_fixture):
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
