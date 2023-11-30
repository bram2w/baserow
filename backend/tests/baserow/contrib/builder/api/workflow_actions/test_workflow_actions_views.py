from django.urls import reverse

import pytest
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
)

from baserow.contrib.builder.workflow_actions.handler import (
    BuilderWorkflowActionHandler,
)
from baserow.contrib.builder.workflow_actions.workflow_action_types import (
    NotificationWorkflowActionType,
)
from baserow.core.formula.serializers import FormulaSerializerField


@pytest.mark.django_db
def test_create_workflow_action(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    page = data_fixture.create_builder_page(user=user)
    element = data_fixture.create_builder_button_element(page=page)
    workflow_action_type = NotificationWorkflowActionType.type

    url = reverse("api:builder:workflow_action:list", kwargs={"page_id": page.id})
    response = api_client.post(
        url,
        {"type": workflow_action_type, "event": "click", "element_id": element.id},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["type"] == workflow_action_type
    assert response_json["element_id"] == element.id


@pytest.mark.django_db
def test_create_workflow_action_page_does_not_exist(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    workflow_action_type = NotificationWorkflowActionType.type

    url = reverse("api:builder:workflow_action:list", kwargs={"page_id": 99999})
    response = api_client.post(
        url,
        {"type": workflow_action_type, "event": "click"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    assert response.status_code == HTTP_404_NOT_FOUND


@pytest.mark.django_db(transaction=True)
def test_create_workflow_action_element_does_not_exist(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    page = data_fixture.create_builder_page(user=user)
    workflow_action_type = NotificationWorkflowActionType.type

    url = reverse("api:builder:workflow_action:list", kwargs={"page_id": page.id})
    response = api_client.post(
        url,
        {"type": workflow_action_type, "event": "click", "element_id": 9999},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    assert response.status_code == HTTP_404_NOT_FOUND


@pytest.mark.django_db(transaction=True)
def test_create_workflow_action_event_does_not_exist(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    page = data_fixture.create_builder_page(user=user)
    workflow_action_type = NotificationWorkflowActionType.type

    url = reverse("api:builder:workflow_action:list", kwargs={"page_id": page.id})
    response = api_client.post(
        url,
        {"type": workflow_action_type, "event": "invalid"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    assert response.status_code == HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_get_workflow_actions(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    page = data_fixture.create_builder_page(user=user)
    workflow_action_one = data_fixture.create_notification_workflow_action(page=page)
    workflow_action_two = data_fixture.create_notification_workflow_action(page=page)

    url = reverse("api:builder:workflow_action:list", kwargs={"page_id": page.id})
    response = api_client.get(
        url,
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert len(response_json) == 2
    assert response_json[0]["id"] == workflow_action_one.id
    assert response_json[1]["id"] == workflow_action_two.id


@pytest.mark.django_db
def test_delete_workflow_actions(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    page = data_fixture.create_builder_page(user=user)
    workflow_action = data_fixture.create_notification_workflow_action(page=page)

    url = reverse(
        "api:builder:workflow_action:item",
        kwargs={"workflow_action_id": workflow_action.id},
    )
    response = api_client.delete(
        url,
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    assert response.status_code == HTTP_204_NO_CONTENT


@pytest.mark.django_db
def test_patch_workflow_actions(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    page = data_fixture.create_builder_page(user=user)
    workflow_action = data_fixture.create_notification_workflow_action(page=page)

    url = reverse(
        "api:builder:workflow_action:item",
        kwargs={"workflow_action_id": workflow_action.id},
    )
    response = api_client.patch(
        url,
        {"description": "'hello'"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["description"] == "'hello'"


class PublicTestWorkflowActionType(NotificationWorkflowActionType):
    type = "test_workflow_action"

    public_serializer_field_names = ["test"]
    public_serializer_field_overrides = {
        "test": FormulaSerializerField(
            required=False,
            allow_blank=True,
            default="",
        ),
    }


@pytest.mark.django_db
def test_public_workflow_actions_view(
    api_client, data_fixture, mutable_builder_workflow_action_registry
):
    user, token = data_fixture.create_user_and_token()
    page = data_fixture.create_builder_page(user=user)

    mutable_builder_workflow_action_registry.unregister(
        NotificationWorkflowActionType().type
    )
    mutable_builder_workflow_action_registry.register(PublicTestWorkflowActionType())

    workflow_action = BuilderWorkflowActionHandler().create_workflow_action(
        PublicTestWorkflowActionType(), test="hello", page=page
    )

    url = reverse(
        "api:builder:workflow_action:item",
        kwargs={"workflow_action_id": workflow_action.id},
    )
    response = api_client.get(
        url,
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    assert "test" not in response.json()

    url = reverse(
        "api:builder:domains:list_workflow_actions",
        kwargs={"page_id": page.id},
    )
    response = api_client.get(
        url,
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    [workflow_action_in_response] = response.json()
    assert "test" in workflow_action_in_response
