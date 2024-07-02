from django.urls import reverse

import pytest
from rest_framework.status import HTTP_200_OK

from baserow.core.user_sources.registries import DEFAULT_USER_ROLE_PREFIX


@pytest.fixture(autouse=True)
def user_source_and_token(data_fixture):
    """A fixture to help test UserSourceSerializer."""

    user, token = data_fixture.create_user_and_token()
    workspace = data_fixture.create_workspace(user=user)
    page = data_fixture.create_builder_page(user=user)
    application = data_fixture.create_builder_application(workspace=workspace)
    user_source = data_fixture.create_user_source_with_first_type(
        application=application,
    )
    return (user_source, token)


@pytest.mark.django_db
def test_list_roles_endpoint_returns_zero_roles_by_default(
    api_client, data_fixture, user_source_and_token
):
    """
    Ensure that a User Source without any results (the default) will return
    an empty list of roles.
    """

    user_source, token = user_source_and_token

    url = reverse(
        "api:user_sources:list_roles",
        kwargs={"application_id": user_source.application.id},
    )
    response = api_client.get(
        url,
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json == [
        {
            "id": user_source.id,
            "roles": [f"{DEFAULT_USER_ROLE_PREFIX}{user_source.id}"],
        }
    ]
