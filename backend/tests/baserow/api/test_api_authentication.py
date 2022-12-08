from django.shortcuts import reverse

import pytest
from freezegun import freeze_time
from rest_framework.status import HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_authenticate(api_client, data_fixture):
    with freeze_time("2020-01-01 12:00"):
        _, token = data_fixture.create_user_and_token()

    response = api_client.get(
        reverse("api:groups:list"),
        format="json",
        HTTP_AUTHORIZATION=f"JWT SOME_WRONG_TOKEN",
    )
    assert response.status_code == HTTP_401_UNAUTHORIZED
    assert response.json()["error"] == "ERROR_INVALID_ACCESS_TOKEN"

    response = api_client.get(
        reverse("api:groups:list"), format="json", HTTP_AUTHORIZATION=f"JWT {token}"
    )
    assert response.status_code == HTTP_401_UNAUTHORIZED
    assert response.json()["error"] == "ERROR_INVALID_ACCESS_TOKEN"
