from unittest.mock import patch

from django.urls import reverse

import pytest
from rest_framework.status import HTTP_200_OK, HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_anonymous_user_cant_trigger_test_email(data_fixture, api_client):
    response = api_client.post(
        reverse("api:health:email_tester"),
        {"target_email": "test@test.com"},
    )
    assert response.status_code == HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_non_staff_user_cant_trigger_test_email(data_fixture, api_client):
    user, token = data_fixture.create_user_and_token()

    response = api_client.get(
        reverse("api:health:email_tester"),
        {"target_email": "test@test.com"},
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_403_FORBIDDEN


@pytest.mark.django_db
@patch("django.core.mail.get_connection")
def test_staff_user_can_trigger_test_email(
    patched_get_connection, data_fixture, api_client
):
    user, token = data_fixture.create_user_and_token(is_staff=True)

    response = api_client.post(
        reverse("api:health:email_tester"),
        {"target_email": "test@test.com"},
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_200_OK
    assert response.json() == {
        "error": None,
        "error_stack": None,
        "error_type": None,
        "succeeded": True,
    }


@pytest.mark.django_db
@patch("django.core.mail.get_connection")
def test_staff_user_can_trigger_test_email_and_see_error_if_fails(
    patched_get_connection, data_fixture, api_client
):
    user, token = data_fixture.create_user_and_token(is_staff=True)

    patched_get_connection.side_effect = Exception("Failed")
    response = api_client.post(
        reverse("api:health:email_tester"),
        {"target_email": "test@test.com"},
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_200_OK
    json = response.json()
    assert not json["succeeded"]
    assert json["error"] == "Failed"
    assert json["error_type"] == "Exception"
    assert len(json["error_stack"]) > 1
