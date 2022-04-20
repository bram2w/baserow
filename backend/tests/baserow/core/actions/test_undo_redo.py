from typing import cast
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model

from baserow.core.action.handler import ActionHandler
from baserow.core.action.registries import (
    action_type_registry,
    ActionScopeStr,
)
from baserow.core.actions import DeleteGroupActionType, CreateGroupActionType
from baserow.core.handler import CoreHandler
from baserow.core.models import Group, GROUP_USER_PERMISSION_ADMIN
from baserow.api.sessions import set_untrusted_client_session_id

User = get_user_model()


@pytest.mark.django_db
def test_undoing_action_with_matching_session_and_category_undoes(data_fixture):
    session_id = "session-id"
    user = data_fixture.create_user(session_id=session_id)

    action_type_registry.get_by_type(CreateGroupActionType).do(user, group_name="test")

    ActionHandler.undo(user, [CreateGroupActionType.scope()], session_id)

    assert not Group.objects.exists()


@pytest.mark.django_db
def test_undoing_action_with_matching_session_and_not_matching_category_does_nothing(
    data_fixture,
):
    session_id = "session-id"
    user = data_fixture.create_user(session_id=session_id)

    group_user = action_type_registry.get_by_type(CreateGroupActionType).do(
        user, group_name="test"
    )

    fake_category_which_wont_match = cast(
        ActionScopeStr,
        CreateGroupActionType.scope() + "_fake_category_which_wont_match",
    )
    action = ActionHandler.undo(user, [fake_category_which_wont_match], session_id)

    assert action is None
    assert Group.objects.filter(id=group_user.group_id).exists()


@pytest.mark.django_db
def test_undoing_action_with_not_matching_session_and_not_matching_category_does_nothing(
    data_fixture,
):
    session_id = "session-id"
    user = data_fixture.create_user(session_id=session_id)

    group_user = action_type_registry.get_by_type(CreateGroupActionType).do(
        user, group_name="test"
    )

    fake_category_which_wont_match = cast(
        ActionScopeStr,
        CreateGroupActionType.scope() + "_fake_category_which_wont_match",
    )
    other_session_which_wont_match = session_id + "_fake"
    action = ActionHandler.undo(
        user, [fake_category_which_wont_match], other_session_which_wont_match
    )

    assert action is None
    assert Group.objects.filter(id=group_user.group_id).exists()


@pytest.mark.django_db
def test_undoing_action_with_not_matching_session_and_matching_category_does_nothing(
    data_fixture,
):
    session_id = "session-id"
    user = data_fixture.create_user(session_id=session_id)

    group_user = action_type_registry.get_by_type(CreateGroupActionType).do(
        user, group_name="test"
    )

    other_session_which_wont_match = session_id + "_fake"
    action = ActionHandler.undo(
        user,
        [CreateGroupActionType.scope()],
        other_session_which_wont_match,
    )

    assert action is None
    assert Group.objects.filter(id=group_user.group_id).exists()


@pytest.mark.django_db
def test_redoing_action_with_matching_session_and_category_redoes(data_fixture):
    session_id = "session-id"
    user = data_fixture.create_user(session_id=session_id)

    group_user = action_type_registry.get_by_type(CreateGroupActionType).do(
        user, group_name="test"
    )

    action = ActionHandler.undo(user, [CreateGroupActionType.scope()], session_id)

    assert action.is_undone()
    assert not Group.objects.exists()

    action = ActionHandler.redo(user, [CreateGroupActionType.scope()], session_id)

    assert not action.is_undone()
    assert Group.objects.filter(id=group_user.group_id).exists()


@pytest.mark.django_db
def test_redoing_action_with_matching_session_and_not_matching_category_doesnt_redo(
    data_fixture,
):
    session_id = "session-id"
    user = data_fixture.create_user(session_id=session_id)

    action_type_registry.get_by_type(CreateGroupActionType).do(user, group_name="test")

    action = ActionHandler.undo(user, [CreateGroupActionType.scope()], session_id)

    assert action.is_undone()
    assert not Group.objects.exists()

    fake_category_which_wont_match = cast(
        ActionScopeStr,
        CreateGroupActionType.scope() + "_fake_category_which_wont_match",
    )
    action = ActionHandler.redo(user, [fake_category_which_wont_match], session_id)

    assert action is None
    assert not Group.objects.exists()


@pytest.mark.django_db
def test_redoing_action_with_not_matching_session_and_not_matching_category_doesnt_redo(
    data_fixture,
):
    session_id = "session-id"
    user = data_fixture.create_user(session_id=session_id)

    action_type_registry.get_by_type(CreateGroupActionType).do(user, group_name="test")

    action = ActionHandler.undo(user, [CreateGroupActionType.scope()], session_id)

    assert action.is_undone()
    assert not Group.objects.exists()

    fake_category_which_wont_match = cast(
        ActionScopeStr,
        CreateGroupActionType.scope() + "_fake_category_which_wont_match",
    )
    other_session_which_wont_match = session_id + "_fake"

    action = ActionHandler.redo(
        user, [fake_category_which_wont_match], other_session_which_wont_match
    )

    assert action is None
    assert not Group.objects.exists()


@pytest.mark.django_db
def test_redoing_action_with_not_matching_session_and_matching_category_doesnt_redo(
    data_fixture,
):
    session_id = "session-id"
    user = data_fixture.create_user(session_id=session_id)

    action_type_registry.get_by_type(CreateGroupActionType).do(user, group_name="test")

    action = ActionHandler.undo(user, [CreateGroupActionType.scope()], session_id)

    assert action.is_undone()
    assert not Group.objects.exists()

    other_session_which_wont_match = session_id + "_fake"

    action = ActionHandler.redo(
        user,
        [CreateGroupActionType.scope()],
        other_session_which_wont_match,
    )

    assert action is None
    assert not Group.objects.exists()


@pytest.mark.django_db
def test_undoing_with_multiple_sessions_undoes_only_in_provided_session(
    data_fixture,
):
    session_id = "session-id"
    user = data_fixture.create_user(session_id=session_id)
    same_user_with_different_session = User.objects.get(id=user.id)
    set_untrusted_client_session_id(
        same_user_with_different_session, "different-session"
    )

    group_user_from_first_session = action_type_registry.get_by_type(
        CreateGroupActionType
    ).do(user, group_name="test")
    group_user_from_second_session = action_type_registry.get_by_type(
        CreateGroupActionType
    ).do(same_user_with_different_session, group_name="test2")

    action = ActionHandler.undo(user, [CreateGroupActionType.scope()], session_id)
    assert action.is_undone()
    action = ActionHandler.undo(user, [CreateGroupActionType.scope()], session_id)

    assert action is None
    assert not Group.objects.filter(id=group_user_from_first_session.group_id).exists()
    assert Group.objects.filter(id=group_user_from_second_session.group_id).exists()


@pytest.mark.django_db
def test_redoing_with_multiple_sessions_redoes_only_in_provided_session(
    data_fixture,
):
    session_id = "session-id"
    user = data_fixture.create_user(session_id=session_id)
    same_user_with_different_session = User.objects.get(id=user.id)
    other_session_id = "different-session"
    set_untrusted_client_session_id(same_user_with_different_session, other_session_id)

    group_user_from_first_session = action_type_registry.get_by_type(
        CreateGroupActionType
    ).do(user, group_name="test")
    group_user_from_second_session = action_type_registry.get_by_type(
        CreateGroupActionType
    ).do(same_user_with_different_session, group_name="test2")

    ActionHandler.undo(user, [CreateGroupActionType.scope()], session_id)
    ActionHandler.undo(user, [CreateGroupActionType.scope()], other_session_id)
    assert not Group.objects.filter(id=group_user_from_first_session.group_id).exists()
    assert not Group.objects.filter(id=group_user_from_second_session.group_id).exists()

    action = ActionHandler.redo(user, [CreateGroupActionType.scope()], session_id)
    assert not action.is_undone()
    action = ActionHandler.redo(user, [CreateGroupActionType.scope()], session_id)
    assert action is None

    assert Group.objects.filter(id=group_user_from_first_session.group_id).exists()
    assert not Group.objects.filter(id=group_user_from_second_session.group_id).exists()


@pytest.mark.django_db
def test_undoing_with_multiple_users_undoes_only_in_the_own_users_actions(
    data_fixture,
):
    session_id = "session-id"
    user = data_fixture.create_user(session_id=session_id)
    user2 = data_fixture.create_user(session_id=session_id)

    group_created_by_first_user = (
        action_type_registry.get_by_type(CreateGroupActionType)
        .do(user, group_name="test")
        .group
    )
    group_created_by_second_user = (
        action_type_registry.get_by_type(CreateGroupActionType)
        .do(user2, group_name="test2")
        .group
    )

    action = ActionHandler.undo(user, [CreateGroupActionType.scope()], session_id)
    assert action.is_undone()

    action = ActionHandler.undo(user, [CreateGroupActionType.scope()], session_id)
    assert action is None

    assert not Group.objects.filter(id=group_created_by_first_user.id).exists()
    assert Group.objects.filter(id=group_created_by_second_user.id).exists()


@pytest.mark.django_db
def test_redoing_with_multiple_users_redoes_only_in_the_own_users_actions(
    data_fixture,
):
    session_id = "session-id"
    user = data_fixture.create_user(session_id=session_id)
    user2 = data_fixture.create_user(session_id=session_id)

    group_created_by_first_user = (
        action_type_registry.get_by_type(CreateGroupActionType)
        .do(user, group_name="test")
        .group
    )
    group_created_by_second_user = (
        action_type_registry.get_by_type(CreateGroupActionType)
        .do(user2, group_name="test2")
        .group
    )

    user2_action = ActionHandler.undo(
        user2, [CreateGroupActionType.scope()], session_id
    )
    assert user2_action.is_undone()

    action = ActionHandler.undo(user, [CreateGroupActionType.scope()], session_id)
    assert action.is_undone()
    action = ActionHandler.redo(user, [CreateGroupActionType.scope()], session_id)
    assert not action.is_undone()
    action = ActionHandler.redo(user, [CreateGroupActionType.scope()], session_id)
    assert action is None

    assert Group.objects.filter(id=group_created_by_first_user.id).exists()
    assert not Group.objects.filter(id=group_created_by_second_user.id).exists()


@pytest.mark.django_db
def test_when_undo_fails_can_try_undo_next_action(
    data_fixture,
):
    session_id = "session-id"
    user = data_fixture.create_user(session_id=session_id)

    group1 = (
        action_type_registry.get_by_type(CreateGroupActionType)
        .do(user, group_name="test")
        .group
    )
    group2 = (
        action_type_registry.get_by_type(CreateGroupActionType)
        .do(user, group_name="test2")
        .group
    )
    group2.delete()

    undone_action = ActionHandler.undo(
        user, [CreateGroupActionType.scope()], session_id
    )
    assert undone_action.error

    assert Group.objects.filter(id=group1.id).exists()

    ActionHandler.undo(user, [CreateGroupActionType.scope()], session_id)

    assert not Group.objects.filter(id=group1.id).exists()


@pytest.mark.django_db
@patch("baserow.core.signals.group_deleted.send")
def test_when_undo_fails_the_action_is_rolled_back(
    mock_group_deleted,
    data_fixture,
):
    session_id = "session-id"
    user = data_fixture.create_user(session_id=session_id)

    group = (
        action_type_registry.get_by_type(CreateGroupActionType)
        .do(user, group_name="test2")
        .group
    )

    mock_group_deleted.side_effect = Exception(
        "Error that should make the undo rollback"
    )

    undone_action = ActionHandler.undo(
        user, [CreateGroupActionType.scope()], session_id
    )
    assert undone_action.error

    assert Group.objects.filter(id=group.id).exists(), (
        "The group should still exist as the undo transaction should have failed and "
        "rolled back. "
    )


@pytest.mark.django_db
def test_when_undo_fails_can_try_redo_undo_to_try_again(
    data_fixture,
):
    session_id = "session-id"
    user = data_fixture.create_user(session_id=session_id)
    other_user = data_fixture.create_user(session_id=session_id)

    # User A creates a group
    group = (
        action_type_registry.get_by_type(CreateGroupActionType)
        .do(user, group_name="test")
        .group
    )

    # User B deletes the group
    locked_group = CoreHandler().get_group_for_update(group_id=group.id)
    data_fixture.create_user_group(
        group=locked_group,
        user=other_user,
        permissions=GROUP_USER_PERMISSION_ADMIN,
    )
    action_type_registry.get_by_type(DeleteGroupActionType).do(
        other_user, group=locked_group
    )

    # User A tries to Undo the creation of the group, it fails as it has already been
    # deleted.
    undone_action = ActionHandler.undo(
        user, [CreateGroupActionType.scope()], session_id
    )
    assert undone_action.error

    # User B Undoes the deletion, recreating the group
    ActionHandler.undo(other_user, [DeleteGroupActionType.scope()], session_id)

    # User A Redoes which does nothing
    redone_action = ActionHandler.redo(
        user, [CreateGroupActionType.scope()], session_id
    )
    assert redone_action.error

    # User A can now Undo the creation of the group as it exists again
    ActionHandler.undo(user, [CreateGroupActionType.scope()], session_id)

    assert not Group.objects.exists()


@pytest.mark.django_db
def test_when_redo_fails_the_action_is_rolled_back(
    data_fixture,
):
    session_id = "session-id"
    user = data_fixture.create_user(session_id=session_id)

    group = (
        action_type_registry.get_by_type(CreateGroupActionType)
        .do(user, group_name="test2")
        .group
    )
    action_type_registry.get_by_type(DeleteGroupActionType).do(
        user, CoreHandler().get_group_for_update(group.id)
    )

    # Undo the deletion restoring the group.
    ActionHandler.undo(user, [CreateGroupActionType.scope()], session_id)

    with patch("baserow.core.signals.group_deleted.send") as mock_group_deleted_send:
        mock_group_deleted_send.side_effect = Exception(
            "Error that should make the redo rollback"
        )

        # Redo the deletion
        redone_action = ActionHandler.redo(
            user, [CreateGroupActionType.scope()], session_id
        )
    assert redone_action.error

    assert Group.objects.filter(id=group.id).exists(), (
        "The group should still exist as the redo should have rolled back when it "
        "failed. "
    )
