from django.shortcuts import reverse

import pytest
from rest_framework.status import HTTP_200_OK, HTTP_404_NOT_FOUND


@pytest.fixture(autouse=True)
def enable_enterprise_and_roles_for_all_tests_here(enable_enterprise, synced_roles):
    pass


@pytest.mark.django_db
def test_read_team(
    api_client, data_fixture, enterprise_data_fixture, group_compat_timebomb
):
    user, token = data_fixture.create_user_and_token(
        email="test@test.nl", password="password", first_name="Test1"
    )
    workspace = data_fixture.create_workspace(user=user)
    sales = enterprise_data_fixture.create_team(name="Sales", workspace=workspace)

    response = api_client.get(
        reverse(
            "api:enterprise:teams:item",
            kwargs={"team_id": sales.id},
        ),
        **{"HTTP_AUTHORIZATION": f"JWT {token}"},
    )
    assert response.status_code == HTTP_200_OK
    response_json = response.json()
    assert response_json["id"] == sales.id
    assert response_json["name"] == sales.name
    assert response_json["group"] == workspace.id


@pytest.mark.django_db
def test_list_teams(
    api_client, data_fixture, enterprise_data_fixture, group_compat_timebomb
):
    user, token = data_fixture.create_user_and_token(
        email="test@test.nl", password="password", first_name="Test1"
    )
    workspace = data_fixture.create_workspace(user=user)
    sales = enterprise_data_fixture.create_team(name="Sales", workspace=workspace)
    engineering = enterprise_data_fixture.create_team(
        name="Engineering", workspace=workspace
    )

    response = api_client.get(
        reverse("api:enterprise:teams:list", kwargs={"group_id": workspace.id}),
        **{"HTTP_AUTHORIZATION": f"JWT {token}"},
    )
    assert response.status_code == HTTP_200_OK
    response_json = response.json()
    assert len(response_json) == 2
    assert response_json[0]["id"] == sales.id
    assert response_json[0]["name"] == sales.name
    assert response_json[1]["id"] == engineering.id
    assert response_json[1]["name"] == engineering.name


@pytest.mark.django_db
def test_list_search_teams(
    api_client, data_fixture, enterprise_data_fixture, group_compat_timebomb
):
    user, token = data_fixture.create_user_and_token(
        email="test@test.nl", password="password", first_name="Test1"
    )
    workspace = data_fixture.create_workspace(user=user)
    sales = enterprise_data_fixture.create_team(name="Sales", workspace=workspace)
    enterprise_data_fixture.create_team(name="Engineering", workspace=workspace)

    response = api_client.get(
        f'{reverse("api:enterprise:teams:list", kwargs={"group_id": workspace.id})}?search=Sal',
        **{"HTTP_AUTHORIZATION": f"JWT {token}"},
    )
    assert response.status_code == HTTP_200_OK
    response_json = response.json()
    assert len(response_json) == 1
    assert response_json[0]["id"] == sales.id
    assert response_json[0]["name"] == sales.name


@pytest.mark.django_db
def test_create_team(api_client, data_fixture, group_compat_timebomb):
    user, token = data_fixture.create_user_and_token()
    workspace = data_fixture.create_workspace(user=user)

    response = api_client.post(
        reverse("api:enterprise:teams:list", kwargs={"workspace_id": workspace.id}),
        {"name": "Executives", "default_role": "ThisRoleDoesNotExist"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_ROLE_DOES_NOT_EXIST"

    response = api_client.post(
        reverse("api:enterprise:teams:list", kwargs={"workspace_id": workspace.id}),
        {"name": "Executives"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_200_OK
    response_json = response.json()
    assert response_json["name"] == "Executives"
    assert response_json["group"] == workspace.id
