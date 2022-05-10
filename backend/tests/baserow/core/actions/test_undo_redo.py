from datetime import timedelta
from typing import cast, Any
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.db import connection, transaction
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from freezegun import freeze_time

from baserow.api.sessions import set_untrusted_client_session_id
from baserow.contrib.database.fields.actions import UpdateFieldActionType
from baserow.core.action.handler import ActionHandler
from baserow.core.action.models import Action
from baserow.core.action.registries import (
    action_type_registry,
    ActionScopeStr,
    ActionType,
)
from baserow.core.action.scopes import RootActionScopeType
from baserow.core.actions import DeleteGroupActionType, CreateGroupActionType
from baserow.core.handler import CoreHandler
from baserow.core.models import Group, GROUP_USER_PERMISSION_ADMIN

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

    # Do something else in the other session, this should not affect the redo of
    # the first session.
    action_type_registry.get_by_type(CreateGroupActionType).do(
        same_user_with_different_session, group_name="test2"
    )

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


@pytest.mark.django_db(transaction=True)
def test_actions_which_were_updated_less_than_configured_limit_ago_not_cleaned_up(
    data_fixture, settings
):
    now = timezone.now()
    num_minutes_where_actions_shouldnt_be_cleaned = timedelta(
        minutes=int(settings.MINUTES_UNTIL_ACTION_CLEANED_UP) / 2
    )
    with transaction.atomic():
        with freeze_time(now - num_minutes_where_actions_shouldnt_be_cleaned):
            _create_two_no_custom_cleanup_actions(data_fixture)

    with freeze_time(now):
        assert Action.objects.count() == 2
        ActionHandler.clean_up_old_actions()
        assert Action.objects.count() == 2


@pytest.mark.django_db
def test_cleanup_doesnt_do_n_queries_per_action_when_they_have_no_custom_cleanup(
    data_fixture, settings, django_assert_num_queries
):
    now = timezone.now()
    num_minutes_where_actions_will_be_old_for_clean = timedelta(
        minutes=int(settings.MINUTES_UNTIL_ACTION_CLEANED_UP) * 2
    )
    # Make two actions and record the number of queries done.
    with freeze_time(now - num_minutes_where_actions_will_be_old_for_clean):
        _create_two_no_custom_cleanup_actions(data_fixture)

    with freeze_time(now):
        assert Action.objects.count() == 2
        with CaptureQueriesContext(connection) as clean_up_two_actions:
            ActionHandler.clean_up_old_actions()
        assert Action.objects.count() == 0

    # Now make 4 actions and record the number of queries done
    with freeze_time(now - num_minutes_where_actions_will_be_old_for_clean):
        _create_two_no_custom_cleanup_actions(data_fixture)
        _create_two_no_custom_cleanup_actions(data_fixture)

    with freeze_time(now):
        assert Action.objects.count() == 4
        with CaptureQueriesContext(connection) as clean_up_four_actions:
            ActionHandler.clean_up_old_actions()
        assert Action.objects.count() == 0

    # They should be the same as we should be doing a single bulk query to delete all
    # actions without a custom cleanup.
    assert len(clean_up_two_actions.captured_queries) == len(
        clean_up_four_actions.captured_queries
    )


def _create_two_no_custom_cleanup_actions(data_fixture):
    user = data_fixture.create_user()
    group = (
        action_type_registry.get_by_type(CreateGroupActionType)
        .do(user, group_name="test2")
        .group
    )
    action_type_registry.get_by_type(DeleteGroupActionType).do(
        user, CoreHandler().get_group_for_update(group.id)
    )


@pytest.mark.django_db(transaction=True)
def test_cleanup_does_extra_cleanup_for_actions_implementing_it(data_fixture, settings):
    now = timezone.now()
    num_minutes_where_actions_will_be_old_enough_for_cleaning = timedelta(
        minutes=int(settings.MINUTES_UNTIL_ACTION_CLEANED_UP) * 2
    )
    with transaction.atomic():
        with freeze_time(
            now - num_minutes_where_actions_will_be_old_enough_for_cleaning
        ):
            _create_two_no_custom_cleanup_actions(data_fixture)
            _create_an_action_with_custom_cleanup(data_fixture)

    with freeze_time(now):
        assert Action.objects.count() == 3
        ActionHandler.clean_up_old_actions()
        assert Action.objects.count() == 0


@pytest.mark.django_db(transaction=True)
def test_custom_cleanup_failing_doesnt_rollback_other_successful_cleanups(
    data_fixture, settings, mutable_action_registry, django_assert_num_queries
):

    now = timezone.now()
    num_minutes_where_actions_will_be_old_enough_for_cleaning = timedelta(
        minutes=int(settings.MINUTES_UNTIL_ACTION_CLEANED_UP) * 2
    )
    with transaction.atomic():
        with freeze_time(
            now - num_minutes_where_actions_will_be_old_enough_for_cleaning
        ):
            _create_two_no_custom_cleanup_actions(data_fixture)
            _create_an_action_with_custom_cleanup(data_fixture)
        # Make the cleanup action happen later so it is cleaned up last.
        with freeze_time(
            now - num_minutes_where_actions_will_be_old_enough_for_cleaning / 2
        ):
            action_which_will_fail = _create_an_action_with_custom_cleanup_which_raises(
                mutable_action_registry,
                data_fixture,
                cleanup_exception_message="Custom cleanup failed",
            )

    with freeze_time(now):
        assert Action.objects.count() == 4
        with pytest.raises(Exception, match="Custom cleanup failed"):
            ActionHandler.clean_up_old_actions()
        # The other 3 actions were deleted successfully, and only the last one which
        # failed is left.
        assert Action.objects.count() == 1
        assert Action.objects.first().id == action_which_will_fail.id


def _create_an_action_with_custom_cleanup(data_fixture):
    user = data_fixture.create_user()
    text_field = data_fixture.create_text_field(user=user)
    action_type_registry.get_by_type(UpdateFieldActionType).do(
        user, text_field, "boolean"
    )


def _create_an_action_with_custom_cleanup_which_raises(
    mutable_action_registry, data_fixture, cleanup_exception_message
) -> Action:
    class ActionWithCustomCleanupThatAlwaysRaises(ActionType):
        type = "action_with_custom_cleanup_that_always_raises"

        @classmethod
        def clean_up_any_extra_action_data(cls, action_being_cleaned_up: Action):
            raise Exception(cleanup_exception_message)

        @classmethod
        def do(cls, user) -> Action:
            return cls.register_action(user, cls.Params(), cls.scope())

        @classmethod
        def scope(cls, *args, **kwargs) -> ActionScopeStr:
            return RootActionScopeType.value()

        @classmethod
        def undo(cls, user: AbstractUser, params: Any, action_being_undone: Action):
            pass

        @classmethod
        def redo(cls, user: AbstractUser, params: Any, action_being_redone: Action):
            pass

    mutable_action_registry.register(ActionWithCustomCleanupThatAlwaysRaises())

    return mutable_action_registry.get_by_type(
        ActionWithCustomCleanupThatAlwaysRaises
    ).do(data_fixture.create_user())
