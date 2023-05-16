from django.contrib.auth import get_user_model
from django.shortcuts import reverse

import pytest
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST

from baserow.contrib.database.fields.models import TextField
from baserow.core.action.models import Action

User = get_user_model()


@pytest.mark.django_db
@pytest.mark.undo_redo
def test_can_undo_a_database_action_and_get_correct_response_code(
    api_client, data_fixture
):
    user, token = data_fixture.create_user_and_token()
    table = data_fixture.create_database_table(user=user)
    field = data_fixture.create_text_field(user, table=table)

    same_session_id = "test"

    response = api_client.delete(
        reverse("api:database:fields:item", kwargs={"field_id": field.id}),
        format="json",
        HTTP_CLIENTSESSIONID=same_session_id,
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_200_OK

    api_client.patch(
        reverse("api:user:undo"),
        {"scopes": {"table": table.id, "application": table.database.id}},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
        HTTP_CLIENTSESSIONID=same_session_id,
    )
    assert response.status_code == HTTP_200_OK

    assert TextField.objects.filter(id=field.id).exists()
    assert Action.objects.get().is_undone()


@pytest.mark.django_db
@pytest.mark.undo_redo
def test_asking_for_an_unknown_scope_returns_an_error(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    table = data_fixture.create_database_table(user=user)
    field = data_fixture.create_text_field(user, table=table)

    same_session_id = "test"

    response = api_client.delete(
        reverse("api:database:fields:item", kwargs={"field_id": field.id}),
        format="json",
        HTTP_CLIENTSESSIONID=same_session_id,
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_200_OK

    response = api_client.patch(
        reverse("api:user:undo"),
        {
            "scopes": {
                "table": table.id,
                "application": table.database.id,
                "unknown_scope": True,
            }
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
        HTTP_CLIENTSESSIONID=same_session_id,
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_REQUEST_BODY_VALIDATION"
    assert response.json()["detail"] == {
        "scopes": {
            "non_field_errors": [
                {
                    "code": "invalid",
                    "error": "Your request body had the following unknown attributes: "
                    "unknown_scope. Please check the api documentation and only "
                    "provide valid fields.",
                }
            ]
        }
    }

    assert not TextField.objects.filter(id=field.id).exists()
    assert not Action.objects.get().is_undone()
