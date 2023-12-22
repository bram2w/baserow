from datetime import datetime, timezone

from django.shortcuts import reverse
from django.test.utils import override_settings

import pytest
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_400_BAD_REQUEST,
    HTTP_402_PAYMENT_REQUIRED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
)

from baserow.core.models import Workspace


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_list_admin_workspaces(
    api_client, premium_data_fixture, django_assert_num_queries
):
    """
    This endpoint doesn't need to be tested extensively because it uses the same base
    class as the list users endpoint which already has extensive tests. We only need to
    test if the functionality works in a basic form.
    """

    created = datetime(2020, 4, 10, 0, 0, 0).replace(tzinfo=timezone.utc)
    staff_user, staff_token = premium_data_fixture.create_user_and_token(
        is_staff=True, has_active_premium_license=True
    )
    normal_user, normal_token = premium_data_fixture.create_user_and_token(
        has_active_premium_license=True
    )
    workspace_1 = premium_data_fixture.create_workspace(name="A")
    workspace_1.created_on = created
    workspace_1.save()
    workspace_2 = premium_data_fixture.create_workspace(name="B", created_on=created)
    workspace_2.created_on = created
    workspace_2.save()
    template_workspace = premium_data_fixture.create_workspace(
        name="Template", created_on=created
    )
    premium_data_fixture.create_template(workspace=template_workspace)
    premium_data_fixture.create_user_workspace(
        workspace=workspace_1, user=normal_user, permissions="MEMBER"
    )
    premium_data_fixture.create_user_workspace(
        workspace=workspace_2, user=normal_user, permissions="ADMIN"
    )
    premium_data_fixture.create_database_application(workspace=workspace_1)
    premium_data_fixture.create_database_application(workspace=workspace_1)

    response = api_client.get(
        reverse("api:premium:admin:workspaces:list"),
        format="json",
        HTTP_AUTHORIZATION=f"JWT {normal_token}",
    )
    assert response.status_code == HTTP_403_FORBIDDEN

    with django_assert_num_queries(6):
        response = api_client.get(
            reverse("api:premium:admin:workspaces:list"),
            format="json",
            HTTP_AUTHORIZATION=f"JWT {staff_token}",
        )

    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json == {
        "count": 2,
        "next": None,
        "previous": None,
        "results": [
            {
                "id": workspace_1.id,
                "name": workspace_1.name,
                "users": [
                    {
                        "id": normal_user.id,
                        "email": normal_user.email,
                        "permissions": "MEMBER",
                    }
                ],
                "free_users": None,
                "row_count": 0,
                "seats_taken": None,
                "storage_usage": None,
                "application_count": 2,
                "created_on": "2020-04-10T00:00:00Z",
            },
            {
                "id": workspace_2.id,
                "name": workspace_2.name,
                "users": [
                    {
                        "id": normal_user.id,
                        "email": normal_user.email,
                        "permissions": "ADMIN",
                    }
                ],
                "free_users": None,
                "row_count": 0,
                "seats_taken": None,
                "storage_usage": None,
                "application_count": 0,
                "created_on": "2020-04-10T00:00:00Z",
            },
        ],
    }

    response = api_client.get(
        f'{reverse("api:premium:admin:workspaces:list")}?search={workspace_1.name}',
        format="json",
        HTTP_AUTHORIZATION=f"JWT {staff_token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json == {
        "count": 1,
        "next": None,
        "previous": None,
        "results": [
            {
                "id": workspace_1.id,
                "name": workspace_1.name,
                "users": [
                    {
                        "id": normal_user.id,
                        "email": normal_user.email,
                        "permissions": "MEMBER",
                    }
                ],
                "free_users": None,
                "row_count": 0,
                "seats_taken": None,
                "storage_usage": None,
                "application_count": 2,
                "created_on": "2020-04-10T00:00:00Z",
            },
        ],
    }

    response = api_client.get(
        f'{reverse("api:premium:admin:workspaces:list")}?sorts=-name',
        format="json",
        HTTP_AUTHORIZATION=f"JWT {staff_token}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json == {
        "count": 2,
        "next": None,
        "previous": None,
        "results": [
            {
                "id": workspace_2.id,
                "name": workspace_2.name,
                "users": [
                    {
                        "id": normal_user.id,
                        "email": normal_user.email,
                        "permissions": "ADMIN",
                    }
                ],
                "free_users": None,
                "row_count": 0,
                "seats_taken": None,
                "storage_usage": None,
                "application_count": 0,
                "created_on": "2020-04-10T00:00:00Z",
            },
            {
                "id": workspace_1.id,
                "name": workspace_1.name,
                "users": [
                    {
                        "id": normal_user.id,
                        "email": normal_user.email,
                        "permissions": "MEMBER",
                    }
                ],
                "free_users": None,
                "row_count": 0,
                "seats_taken": None,
                "storage_usage": None,
                "application_count": 2,
                "created_on": "2020-04-10T00:00:00Z",
            },
        ],
    }

    premium_data_fixture.remove_all_active_premium_licenses(staff_user)
    response = api_client.get(
        f'{reverse("api:premium:admin:workspaces:list")}',
        format="json",
        HTTP_AUTHORIZATION=f"JWT {staff_token}",
    )
    assert response.status_code == HTTP_402_PAYMENT_REQUIRED
    assert response.json()["error"] == "ERROR_FEATURE_NOT_AVAILABLE"


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_delete_workspace(api_client, premium_data_fixture):
    normal_user, normal_token = premium_data_fixture.create_user_and_token(
        has_active_premium_license=True
    )
    staff_user, staff_token = premium_data_fixture.create_user_and_token(
        is_staff=True, has_active_premium_license=True
    )
    workspace = premium_data_fixture.create_workspace()

    url = reverse("api:premium:admin:workspaces:edit", kwargs={"workspace_id": 99999})
    response = api_client.delete(url, HTTP_AUTHORIZATION=f"JWT {staff_token}")
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_GROUP_DOES_NOT_EXIST"

    url = reverse(
        "api:premium:admin:workspaces:edit", kwargs={"workspace_id": workspace.id}
    )
    response = api_client.delete(url, HTTP_AUTHORIZATION=f"JWT {normal_token}")
    assert response.status_code == HTTP_403_FORBIDDEN

    url = reverse(
        "api:premium:admin:workspaces:edit", kwargs={"workspace_id": workspace.id}
    )
    response = api_client.delete(url, HTTP_AUTHORIZATION=f"JWT {staff_token}")
    assert response.status_code == 204
    assert Workspace.objects.all().count() == 0

    premium_data_fixture.remove_all_active_premium_licenses(staff_user)
    workspace = premium_data_fixture.create_workspace()
    url = reverse(
        "api:premium:admin:workspaces:edit", kwargs={"workspace_id": workspace.id}
    )
    response = api_client.delete(url, HTTP_AUTHORIZATION=f"JWT {staff_token}")
    assert response.status_code == HTTP_402_PAYMENT_REQUIRED
    assert response.json()["error"] == "ERROR_FEATURE_NOT_AVAILABLE"


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_cant_delete_template_workspace(api_client, premium_data_fixture):
    staff_user, staff_token = premium_data_fixture.create_user_and_token(
        is_staff=True, has_active_premium_license=True
    )
    workspace = premium_data_fixture.create_workspace()
    premium_data_fixture.create_template(workspace=workspace)

    url = reverse(
        "api:premium:admin:workspaces:edit", kwargs={"workspace_id": workspace.id}
    )
    response = api_client.delete(url, HTTP_AUTHORIZATION=f"JWT {staff_token}")
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_CANNOT_DELETE_A_TEMPLATE_GROUP"
    assert Workspace.objects.all().count() == 1
