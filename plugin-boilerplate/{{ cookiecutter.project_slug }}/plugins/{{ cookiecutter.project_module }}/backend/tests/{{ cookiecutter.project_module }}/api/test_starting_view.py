import pytest
from django.shortcuts import reverse
from rest_framework.status import HTTP_200_OK


@pytest.mark.django_db
# Yes, you can use fixtures from Baserow! See how we use them in the core repository
# to write tests easily.
def test_can_query_starting_endpoint_as_authed_user(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()

    response = api_client.get(
        reverse("api:{{ cookiecutter.project_module }}:starting"),
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_200_OK


@pytest.mark.django_db
def test_can_query_starting_endpoint_as_anon_user(api_client):
    response = api_client.get(
        reverse("api:{{ cookiecutter.project_module }}:starting"),
    )
    assert response.status_code == HTTP_200_OK
