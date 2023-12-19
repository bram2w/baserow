from django.urls import reverse

import pytest
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_404_NOT_FOUND,
)


@pytest.mark.django_db
def test_update_theme(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    builder = data_fixture.create_builder_application(user=user)

    url = reverse(
        "api:builder:builder_id:theme:update", kwargs={"builder_id": builder.id}
    )
    response = api_client.patch(
        url,
        {"primary_color": "#f00000ff"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["primary_color"] == "#f00000ff"
    assert response_json["secondary_color"] == "#0eaa42ff"


@pytest.mark.django_db
def test_update_theme_user_no_access_to_workspace(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    builder = data_fixture.create_builder_application()

    url = reverse(
        "api:builder:builder_id:theme:update", kwargs={"builder_id": builder.id}
    )
    response = api_client.patch(
        url,
        {"primary_color": "#f00000ff"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    assert response.status_code == HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_update_theme_user_workspace_doesnt_exist(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()

    url = reverse("api:builder:builder_id:theme:update", kwargs={"builder_id": 0})
    response = api_client.patch(
        url,
        {"primary_color": "#f00000ff"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    response_json = response.json()
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response_json["error"] == "ERROR_APPLICATION_DOES_NOT_EXIST"


@pytest.mark.django_db
def test_update_theme_invalid_value(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    builder = data_fixture.create_builder_application(user=user)

    url = reverse(
        "api:builder:builder_id:theme:update", kwargs={"builder_id": builder.id}
    )
    response = api_client.patch(
        url,
        {"heading_1_font_size": "test"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "ERROR_REQUEST_BODY_VALIDATION"
    assert response_json["detail"]["heading_1_font_size"][0]["code"] == "invalid"
