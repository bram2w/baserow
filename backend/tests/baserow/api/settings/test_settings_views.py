import pytest

from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_403_FORBIDDEN

from django.shortcuts import reverse

from baserow.core.models import Settings
from baserow.core.handler import CoreHandler


@pytest.mark.django_db
def test_get_settings(api_client):
    response = api_client.get(reverse("api:settings:get"))
    assert response.status_code == HTTP_200_OK
    response_json = response.json()
    assert response_json["allow_new_signups"] is True

    settings = Settings.objects.first()
    settings.allow_new_signups = False
    settings.save()

    response = api_client.get(reverse("api:settings:get"))
    assert response.status_code == HTTP_200_OK
    response_json = response.json()
    assert response_json["allow_new_signups"] is False


@pytest.mark.django_db
def test_update_settings(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token(is_staff=True)
    user_2, token_2 = data_fixture.create_user_and_token()

    response = api_client.patch(
        reverse("api:settings:update"),
        {"allow_new_signups": False},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token_2}",
    )
    assert response.status_code == HTTP_403_FORBIDDEN
    assert CoreHandler().get_settings().allow_new_signups is True

    response = api_client.patch(
        reverse("api:settings:update"),
        {"allow_new_signups": {}},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    response_json = response.json()
    assert response_json["error"] == "ERROR_REQUEST_BODY_VALIDATION"
    assert response_json["detail"]["allow_new_signups"][0]["code"] == "invalid"

    response = api_client.patch(
        reverse("api:settings:update"),
        {"allow_new_signups": False},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_200_OK
    response_json = response.json()
    assert response_json["allow_new_signups"] is False
    assert CoreHandler().get_settings().allow_new_signups is False

    response = api_client.patch(
        reverse("api:settings:update"),
        {},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_200_OK
    response_json = response.json()
    assert response_json["allow_new_signups"] is False
    assert CoreHandler().get_settings().allow_new_signups is False
