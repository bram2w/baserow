import pytest
from baserow.contrib.database.views.actions import (
    CreateViewFilterActionType,
    DeleteViewFilterActionType,
    UpdateViewFilterActionType,
)
from baserow.contrib.database.views.models import ViewFilter
from baserow.core.action.handler import ActionHandler
from baserow.core.action.registries import action_type_registry
from baserow.core.action.scopes import ViewActionScopeType
from baserow.test_utils.helpers import assert_undo_redo_actions_are_valid


@pytest.mark.django_db
@pytest.mark.undo_redo
def test_can_undo_creating_view_filter(data_fixture):
    session_id = "1010"
    user = data_fixture.create_user(session_id=session_id)
    table = data_fixture.create_database_table(user=user)
    grid_view = data_fixture.create_grid_view(table=table)
    text_field = data_fixture.create_text_field(table=table)

    assert ViewFilter.objects.count() == 0

    view_filter = action_type_registry.get_by_type(CreateViewFilterActionType).do(
        user,
        grid_view,
        text_field,
        "equal",
        "123",
    )

    assert ViewFilter.objects.filter(pk=view_filter.id).count() == 1
    assert view_filter.view.id == grid_view.id
    assert view_filter.field.id == text_field.id
    assert view_filter.type == "equal"
    assert view_filter.value == "123"

    undone_actions = ActionHandler.undo(
        user, [ViewActionScopeType.value(grid_view.id)], session_id
    )
    assert_undo_redo_actions_are_valid(undone_actions, [CreateViewFilterActionType])

    assert ViewFilter.objects.filter(pk=view_filter.id).count() == 0


@pytest.mark.django_db
@pytest.mark.undo_redo
def test_can_undo_redo_creating_view_filter(data_fixture):
    session_id = "1010"
    user = data_fixture.create_user(session_id=session_id)
    table = data_fixture.create_database_table(user=user)
    grid_view = data_fixture.create_grid_view(table=table)
    text_field = data_fixture.create_text_field(table=table)

    assert ViewFilter.objects.count() == 0

    view_filter = action_type_registry.get_by_type(CreateViewFilterActionType).do(
        user,
        grid_view,
        text_field,
        "equal",
        "123",
    )
    original_view_filter_id = view_filter.id

    assert ViewFilter.objects.filter(pk=view_filter.id).count() == 1
    assert view_filter.view.id == grid_view.id
    assert view_filter.field.id == text_field.id
    assert view_filter.type == "equal"
    assert view_filter.value == "123"

    ActionHandler.undo(user, [ViewActionScopeType.value(grid_view.id)], session_id)

    assert ViewFilter.objects.filter(pk=view_filter.id).count() == 0

    redone_actions = ActionHandler.redo(
        user, [ViewActionScopeType.value(grid_view.id)], session_id
    )
    assert_undo_redo_actions_are_valid(redone_actions, [CreateViewFilterActionType])

    assert ViewFilter.objects.filter(pk=view_filter.id).count() == 1
    updated_view_filter = ViewFilter.objects.first()
    assert updated_view_filter.id == original_view_filter_id
    assert updated_view_filter.view.id == grid_view.id
    assert updated_view_filter.field.id == text_field.id
    assert updated_view_filter.type == "equal"
    assert updated_view_filter.value == "123"


@pytest.mark.django_db
@pytest.mark.undo_redo
def test_can_undo_updating_view_filter(data_fixture):
    session_id = "1010"
    user = data_fixture.create_user(session_id=session_id)
    table = data_fixture.create_database_table(user=user)
    grid_view = data_fixture.create_grid_view(table=table)
    text_field = data_fixture.create_text_field(table=table)
    view_filter = data_fixture.create_view_filter(
        view=grid_view, field=text_field, type="equal", value="Test"
    )

    assert view_filter.value == "Test"
    assert view_filter.type == "equal"

    action_type_registry.get_by_type(UpdateViewFilterActionType).do(
        user,
        view_filter,
        filter_value="My new test value",
    )
    action_type_registry.get_by_type(UpdateViewFilterActionType).do(
        user,
        view_filter,
        filter_type="contains",
    )

    view_filter.refresh_from_db()
    assert view_filter.value == "My new test value"
    assert view_filter.type == "contains"

    undone_actions = ActionHandler.undo(
        user, [ViewActionScopeType.value(grid_view.id)], session_id
    )

    assert_undo_redo_actions_are_valid(undone_actions, [UpdateViewFilterActionType])

    view_filter.refresh_from_db()
    assert view_filter.value == "My new test value"
    assert view_filter.type == "equal"

    undone_actions = ActionHandler.undo(
        user, [ViewActionScopeType.value(grid_view.id)], session_id
    )

    assert_undo_redo_actions_are_valid(undone_actions, [UpdateViewFilterActionType])

    view_filter.refresh_from_db()
    assert view_filter.value == "Test"
    assert view_filter.type == "equal"


@pytest.mark.django_db
@pytest.mark.undo_redo
def test_can_undo_redo_updating_view_filter(data_fixture):
    session_id = "1010"
    user = data_fixture.create_user(session_id=session_id)
    table = data_fixture.create_database_table(user=user)
    grid_view = data_fixture.create_grid_view(table=table)
    text_field = data_fixture.create_text_field(table=table)
    view_filter = data_fixture.create_view_filter(
        view=grid_view, field=text_field, type="equal", value="Test"
    )

    assert view_filter.value == "Test"

    action_type_registry.get_by_type(UpdateViewFilterActionType).do(
        user,
        view_filter,
        filter_value="My new test value",
    )

    view_filter.refresh_from_db()
    assert view_filter.value == "My new test value"

    undone_actions = ActionHandler.undo(
        user, [ViewActionScopeType.value(grid_view.id)], session_id
    )

    view_filter.refresh_from_db()
    assert view_filter.value == "Test"

    undone_actions = ActionHandler.redo(
        user, [ViewActionScopeType.value(grid_view.id)], session_id
    )
    assert_undo_redo_actions_are_valid(undone_actions, [UpdateViewFilterActionType])

    view_filter.refresh_from_db()
    assert view_filter.value == "My new test value"


@pytest.mark.django_db
@pytest.mark.undo_redo
def test_can_undo_deleting_view_filter(data_fixture):
    session_id = "1010"
    user = data_fixture.create_user(session_id=session_id)
    table = data_fixture.create_database_table(user=user)
    grid_view = data_fixture.create_grid_view(table=table)
    text_field = data_fixture.create_text_field(table=table)
    view_filter = data_fixture.create_view_filter(
        view=grid_view, field=text_field, type="equal", value="Test"
    )
    original_view_filter_id = view_filter.id

    assert ViewFilter.objects.count() == 1
    assert view_filter.view.id == grid_view.id
    assert view_filter.field.id == text_field.id
    assert view_filter.type == "equal"
    assert view_filter.value == "Test"

    action_type_registry.get_by_type(DeleteViewFilterActionType).do(user, view_filter)

    assert ViewFilter.objects.count() == 0

    undone_actions = ActionHandler.undo(
        user, [ViewActionScopeType.value(grid_view.id)], session_id
    )
    assert_undo_redo_actions_are_valid(undone_actions, [DeleteViewFilterActionType])

    assert ViewFilter.objects.count() == 1
    updated_view_filter = ViewFilter.objects.first()
    assert updated_view_filter.id == original_view_filter_id
    assert updated_view_filter.view.id == grid_view.id
    assert updated_view_filter.field.id == text_field.id
    assert updated_view_filter.type == "equal"
    assert updated_view_filter.value == "Test"


@pytest.mark.django_db
@pytest.mark.undo_redo
def test_can_undo_redo_deleting_view_filter(data_fixture):
    session_id = "1010"
    user = data_fixture.create_user(session_id=session_id)
    table = data_fixture.create_database_table(user=user)
    grid_view = data_fixture.create_grid_view(table=table)
    text_field = data_fixture.create_text_field(table=table)
    view_filter = data_fixture.create_view_filter(
        view=grid_view, field=text_field, type="equal", value="Test"
    )
    assert ViewFilter.objects.count() == 1
    assert view_filter.view.id == grid_view.id
    assert view_filter.field.id == text_field.id
    assert view_filter.type == "equal"
    assert view_filter.value == "Test"

    action_type_registry.get_by_type(DeleteViewFilterActionType).do(user, view_filter)

    assert ViewFilter.objects.count() == 0

    ActionHandler.undo(user, [ViewActionScopeType.value(grid_view.id)], session_id)

    assert ViewFilter.objects.count() == 1

    redone_actions = ActionHandler.redo(
        user, [ViewActionScopeType.value(grid_view.id)], session_id
    )
    assert_undo_redo_actions_are_valid(redone_actions, [DeleteViewFilterActionType])

    assert ViewFilter.objects.count() == 0
