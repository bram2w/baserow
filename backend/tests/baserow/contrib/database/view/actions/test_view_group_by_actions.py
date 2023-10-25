import pytest

from baserow.contrib.database.action.scopes import ViewActionScopeType
from baserow.contrib.database.views.actions import (
    CreateViewGroupByActionType,
    DeleteViewGroupByActionType,
    UpdateViewGroupByActionType,
)
from baserow.contrib.database.views.models import ViewGroupBy
from baserow.core.action.handler import ActionHandler
from baserow.core.action.registries import action_type_registry


@pytest.mark.django_db
@pytest.mark.undo_redo
def test_can_undo_creating_view_group_by(data_fixture):
    session_id = "1010"
    user = data_fixture.create_user(session_id=session_id)
    table = data_fixture.create_database_table(user=user)
    grid_view = data_fixture.create_grid_view(table=table)
    number_field = data_fixture.create_number_field(
        table=table, name="value", number_decimal_places=1
    )

    assert ViewGroupBy.objects.count() == 0

    view_group_by = action_type_registry.get_by_type(CreateViewGroupByActionType).do(
        user, grid_view, number_field, "DESC"
    )

    assert ViewGroupBy.objects.filter(pk=view_group_by.id).count() == 1
    assert view_group_by.view.id == grid_view.id
    assert view_group_by.field.id == number_field.id
    assert view_group_by.order == "DESC"

    ActionHandler.undo(user, [ViewActionScopeType.value(grid_view.id)], session_id)

    assert ViewGroupBy.objects.filter(pk=view_group_by.id).count() == 0


@pytest.mark.django_db
@pytest.mark.undo_redo
def test_can_undo_redo_creating_view_group_by(data_fixture):
    session_id = "1010"
    user = data_fixture.create_user(session_id=session_id)
    table = data_fixture.create_database_table(user=user)
    grid_view = data_fixture.create_grid_view(table=table)
    number_field = data_fixture.create_number_field(
        table=table, name="value", number_decimal_places=1
    )

    assert ViewGroupBy.objects.count() == 0

    view_group_by = action_type_registry.get_by_type(CreateViewGroupByActionType).do(
        user, grid_view, number_field, "DESC"
    )
    original_view_group_by_id = view_group_by.id

    assert ViewGroupBy.objects.filter(pk=view_group_by.id).count() == 1
    assert view_group_by.view.id == grid_view.id
    assert view_group_by.field.id == number_field.id
    assert view_group_by.order == "DESC"

    ActionHandler.undo(user, [ViewActionScopeType.value(grid_view.id)], session_id)

    assert ViewGroupBy.objects.filter(pk=view_group_by.id).count() == 0

    ActionHandler.redo(user, [ViewActionScopeType.value(grid_view.id)], session_id)

    assert ViewGroupBy.objects.filter(pk=view_group_by.id).count() == 1
    updated_view_group_by = ViewGroupBy.objects.first()
    assert updated_view_group_by.id == original_view_group_by_id
    assert updated_view_group_by.view.id == grid_view.id
    assert updated_view_group_by.field.id == number_field.id
    assert updated_view_group_by.order == "DESC"


@pytest.mark.django_db
@pytest.mark.undo_redo
def test_can_undo_updating_view_group_by(data_fixture):
    session_id = "1010"
    user = data_fixture.create_user(session_id=session_id)
    table = data_fixture.create_database_table(user=user)
    grid_view = data_fixture.create_grid_view(table=table)
    text_field = data_fixture.create_text_field(table=table)
    view_group_by = data_fixture.create_view_group_by(
        view=grid_view, field=text_field, order="ASC"
    )

    assert view_group_by.view.id == grid_view.id
    assert view_group_by.field.id == text_field.id
    assert view_group_by.order == "ASC"

    action_type_registry.get_by_type(UpdateViewGroupByActionType).do(
        user, view_group_by, order="DESC"
    )

    view_group_by.refresh_from_db()
    assert view_group_by.order == "DESC"

    ActionHandler.undo(user, [ViewActionScopeType.value(grid_view.id)], session_id)

    view_group_by.refresh_from_db()
    assert view_group_by.order == "ASC"


@pytest.mark.django_db
@pytest.mark.undo_redo
def test_can_undo_redo_updating_view_group_by(data_fixture):
    session_id = "1010"
    user = data_fixture.create_user(session_id=session_id)
    table = data_fixture.create_database_table(user=user)
    grid_view = data_fixture.create_grid_view(table=table)
    text_field = data_fixture.create_text_field(table=table)
    view_group_by = data_fixture.create_view_group_by(
        view=grid_view, field=text_field, order="ASC"
    )

    assert view_group_by.view.id == grid_view.id
    assert view_group_by.field.id == text_field.id
    assert view_group_by.order == "ASC"

    action_type_registry.get_by_type(UpdateViewGroupByActionType).do(
        user, view_group_by, order="DESC"
    )

    view_group_by.refresh_from_db()
    assert view_group_by.order == "DESC"

    ActionHandler.undo(user, [ViewActionScopeType.value(grid_view.id)], session_id)

    view_group_by.refresh_from_db()
    assert view_group_by.order == "ASC"

    ActionHandler.redo(user, [ViewActionScopeType.value(grid_view.id)], session_id)

    view_group_by.refresh_from_db()
    assert view_group_by.order == "DESC"


@pytest.mark.django_db
@pytest.mark.undo_redo
def test_can_undo_deleting_view_group_by(data_fixture):
    session_id = "1010"
    user = data_fixture.create_user(session_id=session_id)
    table = data_fixture.create_database_table(user=user)
    grid_view = data_fixture.create_grid_view(table=table)
    text_field = data_fixture.create_text_field(table=table)
    view_group_by = data_fixture.create_view_group_by(
        view=grid_view, field=text_field, order="ASC"
    )
    original_view_group_by_id = view_group_by.id

    assert ViewGroupBy.objects.count() == 1
    assert view_group_by.view.id == grid_view.id
    assert view_group_by.field.id == text_field.id
    assert view_group_by.order == "ASC"

    action_type_registry.get_by_type(DeleteViewGroupByActionType).do(
        user, view_group_by
    )

    assert ViewGroupBy.objects.count() == 0

    ActionHandler.undo(user, [ViewActionScopeType.value(grid_view.id)], session_id)

    assert ViewGroupBy.objects.count() == 1
    updated_view_group_by = ViewGroupBy.objects.first()
    assert updated_view_group_by.id == original_view_group_by_id
    assert updated_view_group_by.view.id == grid_view.id
    assert updated_view_group_by.field.id == text_field.id
    assert updated_view_group_by.order == "ASC"


@pytest.mark.django_db
@pytest.mark.undo_redo
def test_can_undo_redo_deleting_view_group_by(data_fixture):
    session_id = "1010"
    user = data_fixture.create_user(session_id=session_id)
    table = data_fixture.create_database_table(user=user)
    grid_view = data_fixture.create_grid_view(table=table)
    text_field = data_fixture.create_text_field(table=table)
    view_group_by = data_fixture.create_view_group_by(
        view=grid_view, field=text_field, order="ASC"
    )

    assert ViewGroupBy.objects.count() == 1
    assert view_group_by.view.id == grid_view.id
    assert view_group_by.field.id == text_field.id
    assert view_group_by.order == "ASC"

    action_type_registry.get_by_type(DeleteViewGroupByActionType).do(
        user, view_group_by
    )

    assert ViewGroupBy.objects.count() == 0

    ActionHandler.undo(user, [ViewActionScopeType.value(grid_view.id)], session_id)

    assert ViewGroupBy.objects.count() == 1

    ActionHandler.redo(user, [ViewActionScopeType.value(grid_view.id)], session_id)

    assert ViewGroupBy.objects.count() == 0
