import pytest

from baserow.core.action.scopes import GroupActionScopeType
from baserow.core.action.handler import ActionHandler
from baserow.core.action.registries import action_type_registry
from baserow.core.actions import (
    UpdateApplicationActionType,
    DeleteApplicationActionType,
    OrderApplicationsActionType,
    CreateApplicationActionType,
)
from baserow.core.models import Application


@pytest.mark.django_db
def test_can_undo_redo_order_applications(data_fixture, django_assert_num_queries):
    session_id = "session-id"
    user = data_fixture.create_user(session_id=session_id)
    group = data_fixture.create_group(user=user)
    application_1 = data_fixture.create_database_application(group=group, order=1)
    application_2 = data_fixture.create_database_application(group=group, order=2)

    action_type_registry.get_by_type(OrderApplicationsActionType).do(
        user, group, application_ids_in_order=[application_2.id, application_1.id]
    )

    def check_queryset():
        return list(
            Application.objects.all().order_by("order").values_list("id", flat=True)
        )

    assert check_queryset() == [application_2.id, application_1.id]

    ActionHandler.undo(
        user, [GroupActionScopeType.value(group_id=group.id)], session_id
    )
    assert check_queryset() == [application_1.id, application_2.id]

    ActionHandler.redo(
        user, [GroupActionScopeType.value(group_id=group.id)], session_id
    )
    assert check_queryset() == [application_2.id, application_1.id]


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


@pytest.mark.django_db
def test_can_undo_deleteing_application(data_fixture):
    session_id = "session-id"
    user = data_fixture.create_user(session_id=session_id)
    group = data_fixture.create_group(user=user)
    application_type = "database"
    application_name = "My Application"

    application = action_type_registry.get_by_type(CreateApplicationActionType).do(
        user, group, application_type, name=application_name
    )

    action_type_registry.get_by_type(DeleteApplicationActionType).do(user, application)

    assert Application.objects.filter(pk=application.id).count() == 0

    ActionHandler.undo(
        user, [GroupActionScopeType.value(group_id=group.id)], session_id
    )

    assert Application.objects.filter(pk=application.id).count() == 1


@pytest.mark.django_db
def test_can_undo_redo_deleting_application(data_fixture, django_assert_num_queries):
    session_id = "session-id"
    user = data_fixture.create_user(session_id=session_id)
    group = data_fixture.create_group(user=user)
    application_type = "database"
    application_name = "My Application"

    application = action_type_registry.get_by_type(CreateApplicationActionType).do(
        user, group, application_type, name=application_name
    )

    action_type_registry.get_by_type(DeleteApplicationActionType).do(user, application)

    assert Application.objects.filter(pk=application.id).count() == 0

    ActionHandler.undo(
        user, [GroupActionScopeType.value(group_id=group.id)], session_id
    )

    ActionHandler.redo(
        user, [GroupActionScopeType.value(group_id=group.id)], session_id
    )

    assert Application.objects.filter(pk=application.id).count() == 0


@pytest.mark.django_db
def test_can_undo_updating_application(data_fixture, django_assert_num_queries):
    session_id = "session-id"
    user = data_fixture.create_user(session_id=session_id)
    group = data_fixture.create_group(user=user)
    application_type = "database"
    application_name = "My Application"
    application_name_new = "New application name"

    application = action_type_registry.get_by_type(CreateApplicationActionType).do(
        user, group, application_type, name=application_name
    )

    action_type_registry.get_by_type(UpdateApplicationActionType).do(
        user, application, application_name_new
    )

    assert Application.objects.get(pk=application.id).name == application_name_new

    ActionHandler.undo(
        user, [GroupActionScopeType.value(group_id=group.id)], session_id
    )

    assert Application.objects.get(pk=application.id).name == application_name


@pytest.mark.django_db
def test_can_undo_redo_updating_application(data_fixture, django_assert_num_queries):
    session_id = "session-id"
    user = data_fixture.create_user(session_id=session_id)
    group = data_fixture.create_group(user=user)
    application_type = "database"
    application_name = "My Application"
    application_name_new = "New application name"

    application = action_type_registry.get_by_type(CreateApplicationActionType).do(
        user, group, application_type, name=application_name
    )

    action_type_registry.get_by_type(UpdateApplicationActionType).do(
        user, application, application_name_new
    )

    assert Application.objects.get(pk=application.id).name == application_name_new

    ActionHandler.undo(
        user, [GroupActionScopeType.value(group_id=group.id)], session_id
    )

    ActionHandler.redo(
        user, [GroupActionScopeType.value(group_id=group.id)], session_id
    )

    assert Application.objects.get(pk=application.id).name == application_name_new
