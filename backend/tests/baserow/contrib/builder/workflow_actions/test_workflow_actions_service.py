import pytest

from baserow.contrib.builder.workflow_actions.models import (
    BuilderWorkflowAction,
    EventTypes,
)
from baserow.contrib.builder.workflow_actions.service import (
    BuilderWorkflowActionService,
)
from baserow.contrib.builder.workflow_actions.workflow_action_types import (
    NotificationWorkflowActionType,
)
from baserow.core.exceptions import UserNotInWorkspace


@pytest.mark.django_db
def test_create_workflow_action(data_fixture):
    user = data_fixture.create_user()
    page = data_fixture.create_builder_page(user=user)
    element = data_fixture.create_builder_button_element(page=page)
    event = EventTypes.CLICK
    workflow_action_type = NotificationWorkflowActionType()
    workflow_action = (
        BuilderWorkflowActionService()
        .create_workflow_action(
            user, workflow_action_type, page=page, element=element, event=event
        )
        .specific
    )

    assert workflow_action is not None
    assert workflow_action.element is element
    assert BuilderWorkflowAction.objects.count() == 1


@pytest.mark.django_db
def test_create_workflow_action_no_permissions(data_fixture):
    user = data_fixture.create_user()
    page = data_fixture.create_builder_page()
    element = data_fixture.create_builder_button_element(page=page)
    event = EventTypes.CLICK
    workflow_action_type = NotificationWorkflowActionType()

    with pytest.raises(UserNotInWorkspace):
        BuilderWorkflowActionService().create_workflow_action(
            user, workflow_action_type, page=page, element=element, event=event
        )


@pytest.mark.django_db
def test_delete_workflow_action(data_fixture):
    user = data_fixture.create_user()
    page = data_fixture.create_builder_page(user=user)
    element = data_fixture.create_builder_button_element(page=page)
    event = EventTypes.CLICK
    workflow_action = data_fixture.create_notification_workflow_action(
        page=page, element=element, event=event
    )

    assert BuilderWorkflowAction.objects.count() == 1

    BuilderWorkflowActionService().delete_workflow_action(user, workflow_action)

    assert BuilderWorkflowAction.objects.count() == 0


@pytest.mark.django_db
def test_delete_workflow_action_no_permissions(data_fixture):
    user = data_fixture.create_user()
    page = data_fixture.create_builder_page()
    element = data_fixture.create_builder_button_element(page=page)
    event = EventTypes.CLICK
    workflow_action = data_fixture.create_notification_workflow_action(
        page=page, element=element, event=event
    )

    with pytest.raises(UserNotInWorkspace):
        BuilderWorkflowActionService().delete_workflow_action(user, workflow_action)


@pytest.mark.django_db
def test_update_workflow_action(data_fixture):
    user = data_fixture.create_user()
    page = data_fixture.create_builder_page(user=user)
    element = data_fixture.create_builder_button_element(page=page)
    event = EventTypes.CLICK
    workflow_action = data_fixture.create_notification_workflow_action(
        page=page, element=element, event=event
    )

    element_changed = data_fixture.create_builder_button_element()

    workflow_action = BuilderWorkflowActionService().update_workflow_action(
        user, workflow_action, element=element_changed
    )

    workflow_action.refresh_from_db()
    assert workflow_action.element_id == element_changed.id


@pytest.mark.django_db
def test_update_workflow_action_no_permissions(data_fixture):
    user = data_fixture.create_user()
    page = data_fixture.create_builder_page()
    element = data_fixture.create_builder_button_element(page=page)
    event = EventTypes.CLICK
    workflow_action = data_fixture.create_notification_workflow_action(
        page=page, element=element, event=event
    )

    element_changed = data_fixture.create_builder_button_element()

    with pytest.raises(UserNotInWorkspace):
        BuilderWorkflowActionService().update_workflow_action(
            user, workflow_action, element=element_changed
        )


@pytest.mark.django_db
def test_get_workflow_action(data_fixture):
    user = data_fixture.create_user()
    page = data_fixture.create_builder_page(user=user)
    element = data_fixture.create_builder_button_element(page=page)
    event = EventTypes.CLICK
    workflow_action = data_fixture.create_notification_workflow_action(
        page=page, element=element, event=event
    )

    workflow_action_fetched = BuilderWorkflowActionService().get_workflow_action(
        user, workflow_action.id
    )

    assert workflow_action_fetched.id == workflow_action.id


@pytest.mark.django_db
def test_get_workflow_action_no_permissions(data_fixture):
    user = data_fixture.create_user()
    page = data_fixture.create_builder_page()
    element = data_fixture.create_builder_button_element(page=page)
    event = EventTypes.CLICK
    workflow_action = data_fixture.create_notification_workflow_action(
        page=page, element=element, event=event
    )

    with pytest.raises(UserNotInWorkspace):
        BuilderWorkflowActionService().get_workflow_action(user, workflow_action.id)


@pytest.mark.django_db
def test_get_workflow_actions(data_fixture):
    user = data_fixture.create_user()
    page = data_fixture.create_builder_page(user=user)
    element = data_fixture.create_builder_button_element(page=page)
    event = EventTypes.CLICK
    workflow_action_one = data_fixture.create_notification_workflow_action(
        page=page, element=element, event=event
    )
    workflow_action_two = data_fixture.create_notification_workflow_action(
        page=page, element=element, event=event
    )

    [
        workflow_action_one_fetched,
        workflow_action_two_fetched,
    ] = BuilderWorkflowActionService().get_workflow_actions(user, page)

    assert workflow_action_one_fetched.id == workflow_action_one.id
    assert workflow_action_two_fetched.id == workflow_action_two.id


@pytest.mark.django_db
def test_get_workflow_actions_no_permissions(data_fixture):
    user = data_fixture.create_user()
    page = data_fixture.create_builder_page()
    element = data_fixture.create_builder_button_element(page=page)
    event = EventTypes.CLICK
    workflow_action_one = data_fixture.create_notification_workflow_action(
        page=page, element=element, event=event
    )
    workflow_action_two = data_fixture.create_notification_workflow_action(
        page=page, element=element, event=event
    )

    with pytest.raises(UserNotInWorkspace):
        BuilderWorkflowActionService().get_workflow_actions(user, page)
