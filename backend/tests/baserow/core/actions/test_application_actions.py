import pytest

from baserow.core.action.scopes import GroupActionScopeType
from baserow.core.action.handler import ActionHandler
from baserow.core.action.registries import action_type_registry
from baserow.core.actions import CreateApplicationActionType
from baserow.core.models import Application


@pytest.mark.django_db
def test_can_undo_creating_application(data_fixture, django_assert_num_queries):
    session_id = "session-id"
    user = data_fixture.create_user(session_id=session_id)
    group = data_fixture.create_group(user=user)
    application_type = "database"
    application_name = "My Application"

    application = action_type_registry.get_by_type(CreateApplicationActionType).do(
        user, group, application_type, name=application_name
    )

    ActionHandler.undo(
        user, [GroupActionScopeType.value(group_id=group.id)], session_id
    )

    assert Application.objects.filter(pk=application.id).count() == 0


@pytest.mark.django_db
def test_can_undo_redo_creating_application(data_fixture, django_assert_num_queries):
    session_id = "session-id"
    user = data_fixture.create_user(session_id=session_id)
    group = data_fixture.create_group(user=user)
    application_type = "database"
    application_name = "My Application"

    application = action_type_registry.get_by_type(CreateApplicationActionType).do(
        user, group, application_type, name=application_name
    )

    ActionHandler.undo(
        user, [GroupActionScopeType.value(group_id=group.id)], session_id
    )
    ActionHandler.redo(
        user, [GroupActionScopeType.value(group_id=group.id)], session_id
    )

    assert Application.objects.filter(pk=application.id).count() == 1
