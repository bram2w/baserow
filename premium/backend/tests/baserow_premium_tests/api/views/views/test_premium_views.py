from django.shortcuts import reverse

import pytest
from rest_framework.status import HTTP_200_OK


@pytest.mark.django_db
def test_list_views_ownership_type(
    api_client, data_fixture, alternative_per_workspace_license_service
):
    """
    In premium, both collaborative and personal views are returned.
    """

    workspace = data_fixture.create_workspace(name="Group 1")
    database = data_fixture.create_database_application(workspace=workspace)
    user, token = data_fixture.create_user_and_token(
        workspace=workspace,
        email="test@test.nl",
        password="password",
        first_name="Test1",
    )
    user2, token2 = data_fixture.create_user_and_token(
        workspace=workspace,
        email="test2@test.nl",
        password="password",
        first_name="Test2",
    )
    table_1 = data_fixture.create_database_table(user=user, database=database)
    view_1 = data_fixture.create_grid_view(
        table=table_1, order=1, ownership_type="collaborative", owned_by=user
    )
    view_2 = data_fixture.create_grid_view(
        table=table_1, order=3, ownership_type="personal", owned_by=user
    )
    # view belongs to another user
    view_3 = data_fixture.create_grid_view(
        table=table_1, order=3, ownership_type="personal", owned_by=user2
    )
    alternative_per_workspace_license_service.restrict_user_premium_to(
        user, workspace.id
    )

    response = api_client.get(
        reverse("api:database:views:list", kwargs={"table_id": table_1.id}),
        **{"HTTP_AUTHORIZATION": f"JWT {token}"},
    )

    assert response.status_code == HTTP_200_OK
    response_json = response.json()
    assert len(response_json) == 2
    assert response_json[0]["id"] == view_1.id
    assert response_json[0]["ownership_type"] == "collaborative"
    assert response_json[1]["id"] == view_2.id
    assert response_json[1]["ownership_type"] == "personal"
