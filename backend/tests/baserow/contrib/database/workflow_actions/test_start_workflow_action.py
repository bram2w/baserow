from django.urls import reverse

import pytest
from rest_framework.status import HTTP_200_OK

from baserow.contrib.database.workflow_actions.models import (
    CoreStartWorkflowWorkflowAction,
)


@pytest.mark.django_db
def test_create_a_start_workflow_action(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    table = data_fixture.create_database_table(user=user)
    button_field = data_fixture.create_button_field(table=table)

    response = api_client.post(
        reverse(
            "api:database:workflow_actions:list",
            kwargs={"field_id": button_field.id},
        ),
        {"type": "start_workflow"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    assert response.status_code == HTTP_200_OK, response.json()
    data = response.json()
    assert data["type"] == "start_workflow"
    # The action names its own service type, so the editor never sends it.
    assert data["service"]["type"] == "start_workflow"
    assert CoreStartWorkflowWorkflowAction.objects.count() == 1


@pytest.mark.django_db
def test_a_workflow_the_user_can_read_is_kept(api_client, data_fixture):
    from baserow.contrib.automation.nodes.node_types import CoreManualTriggerNodeType

    user, token = data_fixture.create_user_and_token()
    workspace = data_fixture.create_workspace(user=user)
    database = data_fixture.create_database_application(user=user, workspace=workspace)
    table = data_fixture.create_database_table(user=user, database=database)
    button_field = data_fixture.create_button_field(table=table)
    automation = data_fixture.create_automation_application(
        user=user, workspace=workspace
    )
    workflow = data_fixture.create_automation_workflow(
        user=user,
        automation=automation,
        trigger_type=CoreManualTriggerNodeType.type,
    )
    action = data_fixture.create_database_workflow_action(
        CoreStartWorkflowWorkflowAction, field=button_field
    )

    response = api_client.patch(
        reverse(
            "api:database:workflow_actions:item",
            kwargs={"workflow_action_id": action.id},
        ),
        {"service": {"workflow_id": workflow.id}},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    assert response.status_code == HTTP_200_OK, response.json()
    action.refresh_from_db()
    assert action.service.specific.workflow_id == workflow.id


@pytest.mark.django_db
def test_a_workflow_from_another_workspace_is_refused(api_client, data_fixture):
    """
    The shared service type only checks that the person configuring the
    button may read the workflow, and a user is often in more than one
    workspace. Without this, workspace B's workflow ends up behind workspace
    A's button, where every editor of A can fire it.
    """

    from rest_framework.status import HTTP_400_BAD_REQUEST

    from baserow.contrib.automation.nodes.node_types import CoreManualTriggerNodeType

    user, token = data_fixture.create_user_and_token()
    table = data_fixture.create_database_table(user=user)
    button_field = data_fixture.create_button_field(table=table)
    elsewhere = data_fixture.create_workspace(user=user)
    automation = data_fixture.create_automation_application(
        user=user, workspace=elsewhere
    )
    workflow = data_fixture.create_automation_workflow(
        user=user,
        automation=automation,
        trigger_type=CoreManualTriggerNodeType.type,
    )
    action = data_fixture.create_database_workflow_action(
        CoreStartWorkflowWorkflowAction, field=button_field
    )

    response = api_client.patch(
        reverse(
            "api:database:workflow_actions:item",
            kwargs={"workflow_action_id": action.id},
        ),
        {"service": {"workflow_id": workflow.id}},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    assert response.status_code == HTTP_400_BAD_REQUEST
    action.refresh_from_db()
    assert action.service.specific.workflow_id is None


@pytest.mark.django_db
def test_a_workflow_id_that_is_not_a_workflow_is_refused(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    table = data_fixture.create_database_table(user=user)
    button_field = data_fixture.create_button_field(table=table)
    action = data_fixture.create_database_workflow_action(
        CoreStartWorkflowWorkflowAction, field=button_field
    )

    from rest_framework.status import HTTP_400_BAD_REQUEST

    response = api_client.patch(
        reverse(
            "api:database:workflow_actions:item",
            kwargs={"workflow_action_id": action.id},
        ),
        {"service": {"workflow_id": 0}},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    assert response.status_code == HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_clearing_the_workflow_needs_no_workspace(api_client, data_fixture):
    """An explicit null takes nothing away from anyone, as with a bot in 4c."""

    from rest_framework.status import HTTP_200_OK as OK

    user, token = data_fixture.create_user_and_token()
    table = data_fixture.create_database_table(user=user)
    button_field = data_fixture.create_button_field(table=table)
    action = data_fixture.create_database_workflow_action(
        CoreStartWorkflowWorkflowAction, field=button_field
    )

    response = api_client.patch(
        reverse(
            "api:database:workflow_actions:item",
            kwargs={"workflow_action_id": action.id},
        ),
        {"service": {"workflow_id": None}},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    assert response.status_code == OK, response.json()
