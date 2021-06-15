import pytest

from django.utils.timezone import make_aware, datetime, utc
from django.shortcuts import reverse

from rest_framework.status import (
    HTTP_200_OK,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_400_BAD_REQUEST,
)

from baserow.core.models import Group


@pytest.mark.django_db
def test_list_admin_groups(api_client, data_fixture, django_assert_num_queries):
    """
    This endpoint doesn't need to be tested extensively because it uses the same base
    class as the list users endpoint which already has extensive tests. We only need to
    test if the functionality works in a basic form.
    """

    created = make_aware(datetime(2020, 4, 10, 0, 0, 0), utc)
    staff_user, staff_token = data_fixture.create_user_and_token(is_staff=True)
    normal_user, normal_token = data_fixture.create_user_and_token()
    group_1 = data_fixture.create_group(name="A")
    group_1.created_on = created
    group_1.save()
    group_2 = data_fixture.create_group(name="B", created_on=created)
    group_2.created_on = created
    group_2.save()
    template_group = data_fixture.create_group(name="Template", created_on=created)
    data_fixture.create_template(group=template_group)
    data_fixture.create_user_group(
        group=group_1, user=normal_user, permissions="MEMBER"
    )
    data_fixture.create_user_group(group=group_2, user=normal_user, permissions="ADMIN")
    data_fixture.create_database_application(group=group_1)
    data_fixture.create_database_application(group=group_1)

    response = api_client.get(
        reverse("api:premium:admin:groups:list"),
        format="json",
        HTTP_AUTHORIZATION=f"JWT {normal_token}",
    )
    assert response.status_code == HTTP_403_FORBIDDEN

    with django_assert_num_queries(5):
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
                "created_on": "2020-04-10T00:00:00Z",
            },
        ],
    }


@pytest.mark.django_db
def test_delete_group(api_client, data_fixture):
    normal_user, normal_token = data_fixture.create_user_and_token()
    staff_user, staff_token = data_fixture.create_user_and_token(is_staff=True)
    group = data_fixture.create_group()

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


@pytest.mark.django_db
def test_cant_delete_template_group(api_client, data_fixture):
    staff_user, staff_token = data_fixture.create_user_and_token(is_staff=True)
    group = data_fixture.create_group()
    data_fixture.create_template(group=group)

    url = reverse("api:premium:admin:groups:edit", kwargs={"group_id": group.id})
    response = api_client.delete(url, HTTP_AUTHORIZATION=f"JWT {staff_token}")
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_CANNOT_DELETE_A_TEMPLATE_GROUP"
    assert Group.objects.all().count() == 1
