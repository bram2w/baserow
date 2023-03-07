from django.shortcuts import reverse
from django.test.utils import override_settings
from django.utils.timezone import datetime, make_aware, utc

import pytest
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_400_BAD_REQUEST,
    HTTP_402_PAYMENT_REQUIRED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
)

from baserow.core.models import Group


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_list_admin_groups(api_client, premium_data_fixture, django_assert_num_queries):
    """
    This endpoint doesn't need to be tested extensively because it uses the same base
    class as the list users endpoint which already has extensive tests. We only need to
    test if the functionality works in a basic form.
    """

    created = make_aware(datetime(2020, 4, 10, 0, 0, 0), utc)
    staff_user, staff_token = premium_data_fixture.create_user_and_token(
        is_staff=True, has_active_premium_license=True
    )
    normal_user, normal_token = premium_data_fixture.create_user_and_token(
        has_active_premium_license=True
    )
    group_1 = premium_data_fixture.create_group(name="A")
    group_1.created_on = created
    group_1.save()
    group_2 = premium_data_fixture.create_group(
        name="B", created_on=created, storage_usage=1000
    )
    group_2.created_on = created
    group_2.save()
    template_group = premium_data_fixture.create_group(
        name="Template", created_on=created
    )
    premium_data_fixture.create_template(group=template_group)
    premium_data_fixture.create_user_group(
        group=group_1, user=normal_user, permissions="MEMBER"
    )
    premium_data_fixture.create_user_group(
        group=group_2, user=normal_user, permissions="ADMIN"
    )
    premium_data_fixture.create_database_application(group=group_1)
    database = premium_data_fixture.create_database_application(group=group_1)
    premium_data_fixture.create_database_table(database=database, row_count=2000)

    response = api_client.get(
        reverse("api:premium:admin:groups:list"),
        format="json",
        HTTP_AUTHORIZATION=f"JWT {normal_token}",
    )
    assert response.status_code == HTTP_403_FORBIDDEN

    with django_assert_num_queries(6):
        response = api_client.get(
            reverse("api:premium:admin:groups:list"),
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
                "id": group_1.id,
                "name": group_1.name,
                "users": [
                    {
                        "id": normal_user.id,
                        "email": normal_user.email,
                        "permissions": "MEMBER",
                    }
                ],
                "application_count": 2,
                "free_users": None,
                "seats_taken": None,
                "row_count": 2000,
                "storage_usage": None,
                "created_on": "2020-04-10T00:00:00Z",
            },
            {
                "id": group_2.id,
                "name": group_2.name,
                "users": [
                    {
                        "id": normal_user.id,
                        "email": normal_user.email,
                        "permissions": "ADMIN",
                    }
                ],
                "application_count": 0,
                "free_users": None,
                "seats_taken": None,
                "row_count": 0,
                "storage_usage": 1000,
                "created_on": "2020-04-10T00:00:00Z",
            },
        ],
    }

    response = api_client.get(
        f'{reverse("api:premium:admin:groups:list")}?search={group_1.name}',
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
                "id": group_1.id,
                "name": group_1.name,
                "users": [
                    {
                        "id": normal_user.id,
                        "email": normal_user.email,
                        "permissions": "MEMBER",
                    }
                ],
                "row_count": 2000,
                "storage_usage": None,
                "free_users": None,
                "seats_taken": None,
                "application_count": 2,
                "created_on": "2020-04-10T00:00:00Z",
            },
        ],
    }

    response = api_client.get(
        f'{reverse("api:premium:admin:groups:list")}?sorts=-name',
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
                "id": group_2.id,
                "name": group_2.name,
                "users": [
                    {
                        "id": normal_user.id,
                        "email": normal_user.email,
                        "permissions": "ADMIN",
                    }
                ],
                "row_count": 0,
                "storage_usage": 1000,
                "free_users": None,
                "seats_taken": None,
                "application_count": 0,
                "created_on": "2020-04-10T00:00:00Z",
            },
            {
                "id": group_1.id,
                "name": group_1.name,
                "users": [
                    {
                        "id": normal_user.id,
                        "email": normal_user.email,
                        "permissions": "MEMBER",
                    }
                ],
                "application_count": 2,
                "row_count": 2000,
                "storage_usage": None,
                "free_users": None,
                "seats_taken": None,
                "created_on": "2020-04-10T00:00:00Z",
            },
        ],
    }

    premium_data_fixture.remove_all_active_premium_licenses(staff_user)
    response = api_client.get(
        f'{reverse("api:premium:admin:groups:list")}',
        format="json",
        HTTP_AUTHORIZATION=f"JWT {staff_token}",
    )
    assert response.status_code == HTTP_402_PAYMENT_REQUIRED
    assert response.json()["error"] == "ERROR_FEATURE_NOT_AVAILABLE"


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_delete_group(api_client, premium_data_fixture):
    normal_user, normal_token = premium_data_fixture.create_user_and_token(
        has_active_premium_license=True
    )
    staff_user, staff_token = premium_data_fixture.create_user_and_token(
        is_staff=True, has_active_premium_license=True
    )
    group = premium_data_fixture.create_group()

    url = reverse("api:premium:admin:groups:edit", kwargs={"group_id": 99999})
    response = api_client.delete(url, HTTP_AUTHORIZATION=f"JWT {staff_token}")
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_GROUP_DOES_NOT_EXIST"

    url = reverse("api:premium:admin:groups:edit", kwargs={"group_id": group.id})
    response = api_client.delete(url, HTTP_AUTHORIZATION=f"JWT {normal_token}")
    assert response.status_code == HTTP_403_FORBIDDEN

    url = reverse("api:premium:admin:groups:edit", kwargs={"group_id": group.id})
    response = api_client.delete(url, HTTP_AUTHORIZATION=f"JWT {staff_token}")
    assert response.status_code == 204
    assert Group.objects.all().count() == 0

    premium_data_fixture.remove_all_active_premium_licenses(staff_user)
    group = premium_data_fixture.create_group()
    url = reverse("api:premium:admin:groups:edit", kwargs={"group_id": group.id})
    response = api_client.delete(url, HTTP_AUTHORIZATION=f"JWT {staff_token}")
    assert response.status_code == HTTP_402_PAYMENT_REQUIRED
    assert response.json()["error"] == "ERROR_FEATURE_NOT_AVAILABLE"


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_cant_delete_template_group(api_client, premium_data_fixture):
    staff_user, staff_token = premium_data_fixture.create_user_and_token(
        is_staff=True, has_active_premium_license=True
    )
    group = premium_data_fixture.create_group()
    premium_data_fixture.create_template(group=group)

    url = reverse("api:premium:admin:groups:edit", kwargs={"group_id": group.id})
    response = api_client.delete(url, HTTP_AUTHORIZATION=f"JWT {staff_token}")
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_CANNOT_DELETE_A_TEMPLATE_GROUP"
    assert Group.objects.all().count() == 1
