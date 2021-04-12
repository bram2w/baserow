import pytest
from freezegun import freeze_time

from rest_framework.status import HTTP_401_UNAUTHORIZED

from django.shortcuts import reverse


@pytest.mark.django_db
def test_authenticate(api_client, data_fixture):
    with freeze_time("2020-01-01 12:00"):
        user, token = data_fixture.create_user_and_token()

    response = api_client.get(
        reverse("api:groups:list"), **{"HTTP_AUTHORIZATION": f"JWT SOME_WRONG_TOKEN"}
    )
    assert response.status_code == HTTP_401_UNAUTHORIZED
    assert response.json()["error"] == "ERROR_DECODING_SIGNATURE"

    response = api_client.get(
        reverse("api:groups:list"), **{"HTTP_AUTHORIZATION": f"JWT {token}"}
    )
    assert response.status_code == HTTP_401_UNAUTHORIZED
    assert response.json()["error"] == "ERROR_SIGNATURE_HAS_EXPIRED"
