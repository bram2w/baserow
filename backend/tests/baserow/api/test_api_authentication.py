from django.shortcuts import reverse

import pytest
from freezegun import freeze_time
from rest_framework.status import HTTP_200_OK, HTTP_401_UNAUTHORIZED

from baserow.core.user.handler import UserHandler


@pytest.mark.django_db
def test_authenticate(api_client, data_fixture):
    with freeze_time("2020-01-01 12:00"):
        _, token = data_fixture.create_user_and_token()

    response = api_client.get(
        reverse("api:workspaces:list"),
        format="json",
        HTTP_AUTHORIZATION=f"JWT SOME_WRONG_TOKEN",
    )
    assert response.status_code == HTTP_401_UNAUTHORIZED
    assert response.json()["error"] == "ERROR_INVALID_ACCESS_TOKEN"

    response = api_client.get(
        reverse("api:workspaces:list"), format="json", HTTP_AUTHORIZATION=f"JWT {token}"
    )
    assert response.status_code == HTTP_401_UNAUTHORIZED
    assert response.json()["error"] == "ERROR_INVALID_ACCESS_TOKEN"


@pytest.mark.django_db
def test_access_token_is_invalidated_after_password_change(api_client, data_fixture):
    # without password change
    user, token = data_fixture.create_user_and_token(password="test")

    response = api_client.get(
        reverse("api:workspaces:list"),
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_200_OK

    # with password change
    with freeze_time("2020-01-01 12:01:00"):
        user, token = data_fixture.create_user_and_token(password="test")

    with freeze_time("2020-01-01 12:01:01"):
        UserHandler().change_password(user, "test", "test1234")

        response = api_client.get(
            reverse("api:workspaces:list"),
            format="json",
            HTTP_AUTHORIZATION=f"JWT {token}",
        )
        assert response.status_code == HTTP_401_UNAUTHORIZED
        assert response.json()["error"] == "ERROR_INVALID_ACCESS_TOKEN"
