import pytest

from baserow.contrib.database.action.scopes import ViewActionScopeType
from baserow.contrib.database.views.actions import UpdateViewActionType
from baserow.core.action.handler import ActionHandler
from baserow.core.action.registries import action_type_registry
from baserow.test_utils.helpers import assert_undo_redo_actions_are_valid


@pytest.mark.django_db
@pytest.mark.undo_redo
def test_can_undo_update_view_receive_notification_on_submit(data_fixture):
    session_id = "session-id"
    user = data_fixture.create_user(session_id=session_id)
    table = data_fixture.create_database_table(user=user)
    form_view = data_fixture.create_form_view(table=table)

    def list_users_to_notify_on_submit():
        return [u.id for u in form_view.users_to_notify_on_submit.all()]

    assert list_users_to_notify_on_submit() == []

    action_type_registry.get_by_type(UpdateViewActionType).do(
        user, form_view, receive_notification_on_submit=True
    )

    assert list_users_to_notify_on_submit() == [user.id]

    undone_actions = ActionHandler.undo(
        user, [ViewActionScopeType.value(form_view.id)], session_id
    )
    assert_undo_redo_actions_are_valid(undone_actions, [UpdateViewActionType])

    assert list_users_to_notify_on_submit() == []

    redone_actions = ActionHandler.redo(
        user, [ViewActionScopeType.value(form_view.id)], session_id
    )
    assert_undo_redo_actions_are_valid(redone_actions, [UpdateViewActionType])

    assert list_users_to_notify_on_submit() == [user.id]
