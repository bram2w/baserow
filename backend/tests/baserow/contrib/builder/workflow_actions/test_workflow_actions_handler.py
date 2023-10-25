import pytest

from baserow.contrib.builder.workflow_actions.handler import (
    BuilderWorkflowActionHandler,
)
from baserow.contrib.builder.workflow_actions.models import (
    BuilderWorkflowAction,
    EventTypes,
)
from baserow.contrib.builder.workflow_actions.workflow_action_types import (
    NotificationWorkflowActionType,
    OpenPageWorkflowActionType,
)


@pytest.mark.django_db
def test_create_workflow_action(data_fixture):
    page = data_fixture.create_builder_page()
    element = data_fixture.create_builder_button_element(page=page)
    event = EventTypes.CLICK
    workflow_action_type = NotificationWorkflowActionType()
    workflow_action = (
        BuilderWorkflowActionHandler()
        .create_workflow_action(
            workflow_action_type, page=page, element=element, event=event
        )
        .specific
    )

    assert workflow_action is not None
    assert workflow_action.element is element
    assert BuilderWorkflowAction.objects.count() == 1


@pytest.mark.django_db
def test_delete_workflow_action(data_fixture):
    page = data_fixture.create_builder_page()
    element = data_fixture.create_builder_button_element(page=page)
    event = EventTypes.CLICK
    workflow_action = data_fixture.create_notification_workflow_action(
        page=page, element=element, event=event
    )

    assert BuilderWorkflowAction.objects.count() == 1

    BuilderWorkflowActionHandler().delete_workflow_action(workflow_action)

    assert BuilderWorkflowAction.objects.count() == 0


@pytest.mark.django_db
def test_update_workflow_action(data_fixture):
    page = data_fixture.create_builder_page()
    element = data_fixture.create_builder_button_element(page=page)
    event = EventTypes.CLICK
    workflow_action = data_fixture.create_notification_workflow_action(
        page=page, element=element, event=event
    )

    element_changed = data_fixture.create_builder_button_element()

    workflow_action = BuilderWorkflowActionHandler().update_workflow_action(
        workflow_action, element=element_changed
    )

    workflow_action.refresh_from_db()
    assert workflow_action.element_id == element_changed.id


@pytest.mark.django_db
def test_update_workflow_action_type_switching(data_fixture):
    page = data_fixture.create_builder_page()
    element = data_fixture.create_builder_button_element(page=page)
    event = EventTypes.CLICK
    workflow_action = data_fixture.create_notification_workflow_action(
        page=page, element=element, event=event
    )

    workflow_action_changed = BuilderWorkflowActionHandler().update_workflow_action(
        workflow_action, type=OpenPageWorkflowActionType.type, url="'hello'"
    )

    assert workflow_action_changed.get_type().type == OpenPageWorkflowActionType.type
    assert workflow_action_changed.url == "'hello'"
    assert workflow_action_changed.event == event
    assert workflow_action_changed.page_id == page.id
    assert workflow_action_changed.element_id == element.id


@pytest.mark.django_db
def test_get_workflow_action(data_fixture):
    page = data_fixture.create_builder_page()
    element = data_fixture.create_builder_button_element(page=page)
    event = EventTypes.CLICK
    workflow_action = data_fixture.create_notification_workflow_action(
        page=page, element=element, event=event
    )

    workflow_action_fetched = BuilderWorkflowActionHandler().get_workflow_action(
        workflow_action.id
    )

    assert workflow_action_fetched.id == workflow_action.id


@pytest.mark.django_db
def test_get_workflow_actions(data_fixture):
    page = data_fixture.create_builder_page()
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
    ] = BuilderWorkflowActionHandler().get_workflow_actions(page)

    assert workflow_action_one_fetched.id == workflow_action_one.id
    assert workflow_action_two_fetched.id == workflow_action_two.id
