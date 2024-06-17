import pytest

from baserow.contrib.database.action.scopes import ViewActionScopeType
from baserow.contrib.database.views.actions import (
    CreateViewFilterActionType,
    CreateViewFilterGroupActionType,
    DeleteViewFilterActionType,
    DeleteViewFilterGroupActionType,
    UpdateViewFilterActionType,
    UpdateViewFilterGroupActionType,
)
from baserow.contrib.database.views.models import ViewFilter, ViewFilterGroup
from baserow.core.action.handler import ActionHandler
from baserow.core.action.registries import action_type_registry
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

    ActionHandler.undo(user, [ViewActionScopeType.value(grid_view.id)], session_id)

    view_filter.refresh_from_db()
    assert view_filter.value == "Test"

    redone_actions = ActionHandler.redo(
        user, [ViewActionScopeType.value(grid_view.id)], session_id
    )
    assert_undo_redo_actions_are_valid(redone_actions, [UpdateViewFilterActionType])

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


@pytest.mark.django_db
@pytest.mark.undo_redo
def test_can_undo_creating_view_filter_group(data_fixture):
    session_id = "1010"
    user = data_fixture.create_user(session_id=session_id)
    table = data_fixture.create_database_table(user=user)
    grid_view = data_fixture.create_grid_view(table=table)

    assert ViewFilterGroup.objects.count() == 0

    view_filter = action_type_registry.get_by_type(CreateViewFilterGroupActionType).do(
        user, grid_view
    )

    assert ViewFilterGroup.objects.filter(pk=view_filter.id).count() == 1
    assert view_filter.view.id == grid_view.id
    assert view_filter.filter_type == "AND"

    undone_actions = ActionHandler.undo(
        user, [ViewActionScopeType.value(grid_view.id)], session_id
    )
    assert_undo_redo_actions_are_valid(
        undone_actions, [CreateViewFilterGroupActionType]
    )

    assert ViewFilter.objects.filter(pk=view_filter.id).count() == 0


@pytest.mark.django_db
@pytest.mark.undo_redo
def test_can_undo_redo_creating_view_filter_group(data_fixture):
    session_id = "1010"
    user = data_fixture.create_user(session_id=session_id)
    table = data_fixture.create_database_table(user=user)
    grid_view = data_fixture.create_grid_view(table=table)

    assert ViewFilterGroup.objects.count() == 0

    view_filter_group = action_type_registry.get_by_type(
        CreateViewFilterGroupActionType
    ).do(user, grid_view, "OR")

    assert ViewFilterGroup.objects.filter(pk=view_filter_group.id).count() == 1
    assert view_filter_group.view.id == grid_view.id
    assert view_filter_group.filter_type == "OR"
    original_view_filter_group_id = view_filter_group.id

    ActionHandler.undo(user, [ViewActionScopeType.value(grid_view.id)], session_id)

    assert ViewFilterGroup.objects.filter(pk=view_filter_group.id).count() == 0

    redone_actions = ActionHandler.redo(
        user, [ViewActionScopeType.value(grid_view.id)], session_id
    )
    assert_undo_redo_actions_are_valid(
        redone_actions, [CreateViewFilterGroupActionType]
    )

    assert ViewFilterGroup.objects.filter(pk=view_filter_group.id).count() == 1
    restored_view_filter_group = ViewFilterGroup.objects.first()
    assert restored_view_filter_group.id == original_view_filter_group_id
    assert restored_view_filter_group.view.id == grid_view.id
    assert restored_view_filter_group.filter_type == "OR"


@pytest.mark.django_db
@pytest.mark.undo_redo
def test_can_undo_updating_view_filter_group(data_fixture):
    session_id = "1010"
    user = data_fixture.create_user(session_id=session_id)
    table = data_fixture.create_database_table(user=user)
    grid_view = data_fixture.create_grid_view(table=table)
    view_filter_group = data_fixture.create_view_filter_group(view=grid_view)

    assert view_filter_group.id is not None
    assert view_filter_group.filter_type == "AND"

    action_type_registry.get_by_type(UpdateViewFilterGroupActionType).do(
        user, view_filter_group, filter_type="OR"
    )

    view_filter_group.refresh_from_db()
    assert view_filter_group.filter_type == "OR"

    undone_actions = ActionHandler.undo(
        user, [ViewActionScopeType.value(grid_view.id)], session_id
    )

    assert_undo_redo_actions_are_valid(
        undone_actions, [UpdateViewFilterGroupActionType]
    )

    view_filter_group.refresh_from_db()
    assert view_filter_group.filter_type == "AND"


@pytest.mark.django_db
@pytest.mark.undo_redo
def test_can_undo_redo_updating_view_filter_group(data_fixture):
    session_id = "1010"
    user = data_fixture.create_user(session_id=session_id)
    table = data_fixture.create_database_table(user=user)
    grid_view = data_fixture.create_grid_view(table=table)
    view_filter_group = data_fixture.create_view_filter_group(view=grid_view)

    assert view_filter_group.id is not None
    assert view_filter_group.filter_type == "AND"

    action_type_registry.get_by_type(UpdateViewFilterGroupActionType).do(
        user, view_filter_group, filter_type="OR"
    )

    view_filter_group.refresh_from_db()
    assert view_filter_group.filter_type == "OR"

    ActionHandler.undo(user, [ViewActionScopeType.value(grid_view.id)], session_id)

    redone_actions = ActionHandler.redo(
        user, [ViewActionScopeType.value(grid_view.id)], session_id
    )
    assert_undo_redo_actions_are_valid(
        redone_actions, [UpdateViewFilterGroupActionType]
    )

    view_filter_group.refresh_from_db()
    assert view_filter_group.filter_type == "OR"


@pytest.mark.django_db
@pytest.mark.undo_redo
def test_can_undo_deleting_view_filter_group(data_fixture):
    session_id = "1010"
    user = data_fixture.create_user(session_id=session_id)
    table = data_fixture.create_database_table(user=user)
    grid_view = data_fixture.create_grid_view(table=table)
    text_field = data_fixture.create_text_field(table=table)
    view_filter_group = data_fixture.create_view_filter_group(view=grid_view)
    view_filter = data_fixture.create_view_filter(
        view=grid_view,
        field=text_field,
        type="equal",
        value="Test",
        group=view_filter_group,
    )
    original_view_filter_id = view_filter.id
    original_view_filter_group_id = view_filter_group.id

    assert ViewFilterGroup.objects.count() == 1
    assert ViewFilter.objects.count() == 1
    assert view_filter_group.view.id == grid_view.id
    assert [f.id for f in view_filter_group.filters.all()] == [original_view_filter_id]

    action_type_registry.get_by_type(DeleteViewFilterGroupActionType).do(
        user, view_filter_group
    )

    # deleting the group should also delete the filters in a single action
    assert ViewFilterGroup.objects.count() == 0
    assert ViewFilter.objects.count() == 0

    undone_actions = ActionHandler.undo(
        user, [ViewActionScopeType.value(grid_view.id)], session_id
    )
    assert_undo_redo_actions_are_valid(
        undone_actions, [DeleteViewFilterGroupActionType]
    )

    assert ViewFilterGroup.objects.count() == 1
    restored_view_filter_group = ViewFilterGroup.objects.first()
    assert restored_view_filter_group.id == original_view_filter_group_id
    assert [f.id for f in restored_view_filter_group.filters.all()] == [
        original_view_filter_id
    ]


@pytest.mark.django_db
@pytest.mark.undo_redo
def test_can_undo_redo_deleting_view_filter_group(data_fixture):
    session_id = "1010"
    user = data_fixture.create_user(session_id=session_id)
    table = data_fixture.create_database_table(user=user)
    grid_view = data_fixture.create_grid_view(table=table)
    text_field = data_fixture.create_text_field(table=table)
    view_filter_group = data_fixture.create_view_filter_group(view=grid_view)
    view_filter = data_fixture.create_view_filter(
        view=grid_view,
        field=text_field,
        type="equal",
        value="Test",
        group=view_filter_group,
    )

    assert ViewFilterGroup.objects.count() == 1
    assert ViewFilter.objects.count() == 1
    assert view_filter_group.view.id == grid_view.id
    assert [f.id for f in view_filter_group.filters.all()] == [view_filter.id]

    action_type_registry.get_by_type(DeleteViewFilterGroupActionType).do(
        user, view_filter_group
    )

    # deleting the group should also delete the filters in a single action
    assert ViewFilterGroup.objects.count() == 0
    assert ViewFilter.objects.count() == 0

    ActionHandler.undo(user, [ViewActionScopeType.value(grid_view.id)], session_id)

    redone_actions = ActionHandler.redo(
        user, [ViewActionScopeType.value(grid_view.id)], session_id
    )
    assert_undo_redo_actions_are_valid(
        redone_actions, [DeleteViewFilterGroupActionType]
    )

    assert ViewFilterGroup.objects.count() == 0
    assert ViewFilter.objects.count() == 0


@pytest.mark.django_db
@pytest.mark.undo_redo
def test_can_undo_redo_deleting_view_filter_group_with_nested_filters_and_groups(
    data_fixture,
):
    session_id = "1010"
    user = data_fixture.create_user(session_id=session_id)
    table = data_fixture.create_database_table(user=user)
    grid_view = data_fixture.create_grid_view(table=table)
    text_field = data_fixture.create_text_field(table=table)
    view_filter_group = data_fixture.create_view_filter_group(view=grid_view)
    view_filter = data_fixture.create_view_filter(
        view=grid_view,
        field=text_field,
        type="equal",
        value="Test",
        group=view_filter_group,
    )
    nested_group_1 = data_fixture.create_view_filter_group(
        view=grid_view, parent_group=view_filter_group
    )
    view_filter_1 = data_fixture.create_view_filter(
        view=grid_view,
        field=text_field,
        type="equal",
        value="Test",
        group=nested_group_1,
    )
    nested_group_2 = data_fixture.create_view_filter_group(
        view=grid_view, parent_group=nested_group_1
    )
    view_filter_2 = data_fixture.create_view_filter(
        view=grid_view,
        field=text_field,
        type="equal",
        value="Test",
        group=nested_group_2,
    )

    created_filters = [
        {"id": view_filter.id, "group_id": view_filter_group.id},
        {"id": view_filter_1.id, "group_id": nested_group_1.id},
        {"id": view_filter_2.id, "group_id": nested_group_2.id},
    ]

    created_groups = [
        {"id": view_filter_group.id, "parent_group_id": None},
        {"id": nested_group_1.id, "parent_group_id": view_filter_group.id},
        {"id": nested_group_2.id, "parent_group_id": nested_group_1.id},
    ]

    assert ViewFilterGroup.objects.count() == 3
    assert ViewFilter.objects.count() == 3

    action_type_registry.get_by_type(DeleteViewFilterGroupActionType).do(
        user, view_filter_group
    )

    # deleting the group should also delete nested filters and groups in a single action
    assert ViewFilterGroup.objects.count() == 0
    assert ViewFilter.objects.count() == 0

    undone_actions = ActionHandler.undo(
        user, [ViewActionScopeType.value(grid_view.id)], session_id
    )
    assert_undo_redo_actions_are_valid(
        undone_actions, [DeleteViewFilterGroupActionType]
    )

    assert ViewFilterGroup.objects.count() == 3
    assert ViewFilter.objects.count() == 3

    assert (
        list(ViewFilterGroup.objects.values("id", "parent_group_id").order_by("id"))
        == created_groups
    )
    assert (
        list(ViewFilter.objects.values("id", "group_id").order_by("id"))
        == created_filters
    )

    redone_actions = ActionHandler.redo(
        user, [ViewActionScopeType.value(grid_view.id)], session_id
    )
    assert_undo_redo_actions_are_valid(
        redone_actions, [DeleteViewFilterGroupActionType]
    )

    assert ViewFilterGroup.objects.count() == 0
    assert ViewFilter.objects.count() == 0
