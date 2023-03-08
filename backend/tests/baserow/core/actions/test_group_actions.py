from typing import cast

import pytest

from baserow.core.action.handler import ActionHandler
from baserow.core.action.registries import action_type_registry
from baserow.core.action.scopes import RootActionScopeType
from baserow.core.actions import (
    CreateGroupActionType,
    LeaveGroupActionType,
    OrderGroupsActionType,
    UpdateGroupActionType,
)
from baserow.core.exceptions import GroupUserIsLastAdmin
from baserow.core.handler import CoreHandler, GroupForUpdate
from baserow.core.models import Group


@pytest.mark.django_db
@pytest.mark.undo_redo
def test_can_undo_creating_group(data_fixture, django_assert_num_queries):
    session_id = "session-id"
    user = data_fixture.create_user(session_id=session_id)

    group_user = action_type_registry.get_by_type(CreateGroupActionType).do(
        user, "test"
    )
    group = group_user.group

    ActionHandler.undo(user, [RootActionScopeType.value()], session_id)

    assert Group.objects.filter(pk=group.id).count() == 0


@pytest.mark.django_db
@pytest.mark.undo_redo
def test_can_undo_redo_creating_group(data_fixture, django_assert_num_queries):
    session_id = "session-id"
    user = data_fixture.create_user(session_id=session_id)

    group_user = action_type_registry.get_by_type(CreateGroupActionType).do(
        user, "test"
    )
    group2_user = action_type_registry.get_by_type(CreateGroupActionType).do(
        user, "test2"
    )
    group = group_user.group
    group2 = group2_user.group

    ActionHandler.undo(user, [RootActionScopeType.value()], session_id)

    assert not Group.objects.filter(pk=group2.id).exists()
    assert Group.objects.filter(pk=group.id).exists()

    ActionHandler.redo(user, [RootActionScopeType.value()], session_id)

    assert Group.objects.filter(pk=group2.id).exists()
    assert Group.objects.filter(pk=group.id).exists()


@pytest.mark.django_db
@pytest.mark.undo_redo
def test_can_undo_updating_group(data_fixture, django_assert_num_queries):
    session_id = "session-id"
    user = data_fixture.create_user(session_id=session_id)

    group_user = action_type_registry.get_by_type(CreateGroupActionType).do(
        user, "test"
    )

    updated_group = action_type_registry.get_by_type(UpdateGroupActionType).do(
        user, cast(GroupForUpdate, group_user.group), "new name"
    )

    assert updated_group.name == "new name"
    ActionHandler.undo(user, [RootActionScopeType.value()], session_id)
    updated_group.refresh_from_db()
    assert updated_group.name == "test"


@pytest.mark.django_db
@pytest.mark.undo_redo
def test_can_undo_ordering_group(data_fixture, django_assert_num_queries):
    session_id = "session-id"
    user = data_fixture.create_user(session_id=session_id)

    group_user = action_type_registry.get_by_type(CreateGroupActionType).do(
        user, "test"
    )

    group2_user = action_type_registry.get_by_type(CreateGroupActionType).do(
        user, "test2"
    )

    action_type_registry.get_by_type(OrderGroupsActionType).do(
        user, [group_user.group.id, group2_user.group.id]
    )

    order_original = CoreHandler().get_groups_order(user)

    assert order_original == [group_user.group.id, group2_user.group.id]

    order_new = [group2_user.group.id, group_user.group.id]

    action_type_registry.get_by_type(OrderGroupsActionType).do(user, order_new)

    order = CoreHandler().get_groups_order(user)

    assert order == order_new

    ActionHandler.undo(user, [RootActionScopeType.value()], session_id)

    order = CoreHandler().get_groups_order(user)

    assert order == order_original


@pytest.mark.django_db
@pytest.mark.undo_redo
def test_can_undo_redo_ordering_group(data_fixture, django_assert_num_queries):
    session_id = "session-id"
    user = data_fixture.create_user(session_id=session_id)

    group_user = action_type_registry.get_by_type(CreateGroupActionType).do(
        user, "test"
    )

    group2_user = action_type_registry.get_by_type(CreateGroupActionType).do(
        user, "test2"
    )

    action_type_registry.get_by_type(OrderGroupsActionType).do(
        user, [group_user.group.id, group2_user.group.id]
    )

    order_original = CoreHandler().get_groups_order(user)

    assert order_original == [group_user.group.id, group2_user.group.id]

    order_new = [group2_user.group.id, group_user.group.id]

    action_type_registry.get_by_type(OrderGroupsActionType).do(user, order_new)

    order = CoreHandler().get_groups_order(user)

    assert order == order_new

    ActionHandler.undo(user, [RootActionScopeType.value()], session_id)

    order = CoreHandler().get_groups_order(user)

    assert order == order_original

    ActionHandler.redo(user, [RootActionScopeType.value()], session_id)

    order = CoreHandler().get_groups_order(user)

    assert order == order_new


@pytest.mark.django_db
def test_leave_group(data_fixture):
    user = data_fixture.create_user()
    group = data_fixture.create_group(user=user)

    with pytest.raises(GroupUserIsLastAdmin):
        action_type_registry.get(LeaveGroupActionType.type).do(user, group)

    second_user = data_fixture.create_user(group=group)
    action_type_registry.get(LeaveGroupActionType.type).do(second_user, group)

    assert group.users.count() == 1
