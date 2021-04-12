import pytest

from rest_framework.status import (
    HTTP_200_OK,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
)

from django.shortcuts import reverse

from baserow.core.models import GroupUser


@pytest.mark.django_db
def test_list_group_users(api_client, data_fixture):
    user_1, token_1 = data_fixture.create_user_and_token(email="test1@test.nl")
    user_2, token_2 = data_fixture.create_user_and_token(email="test2@test.nl")
    user_3, token_3 = data_fixture.create_user_and_token(email="test3@test.nl")
    group_1 = data_fixture.create_group()
    data_fixture.create_user_group(group=group_1, user=user_1, permissions="ADMIN")
    data_fixture.create_user_group(group=group_1, user=user_2, permissions="MEMBER")

    response = api_client.get(
        reverse("api:groups:users:list", kwargs={"group_id": 99999}),
        {"permissions": "MEMBER"},
        HTTP_AUTHORIZATION=f"JWT {token_1}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response_json["error"] == "ERROR_GROUP_DOES_NOT_EXIST"

    response = api_client.get(
        reverse("api:groups:users:list", kwargs={"group_id": group_1.id}),
        HTTP_AUTHORIZATION=f"JWT {token_3}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "ERROR_USER_NOT_IN_GROUP"

    response = api_client.get(
        reverse("api:groups:users:list", kwargs={"group_id": group_1.id}),
        HTTP_AUTHORIZATION=f"JWT {token_2}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "ERROR_USER_INVALID_GROUP_PERMISSIONS"

    response = api_client.get(
        reverse("api:groups:users:list", kwargs={"group_id": group_1.id}),
        HTTP_AUTHORIZATION=f"JWT {token_1}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert len(response_json) == 2
    assert response_json[0]["permissions"] == "ADMIN"
    assert response_json[0]["name"] == user_1.first_name
    assert response_json[0]["email"] == user_1.email
    assert "created_on" in response_json[0]
    assert response_json[1]["permissions"] == "MEMBER"
    assert response_json[1]["name"] == user_2.first_name
    assert response_json[1]["email"] == user_2.email
    assert "created_on" in response_json[1]


@pytest.mark.django_db
def test_update_group_user(api_client, data_fixture):
    user_1, token_1 = data_fixture.create_user_and_token(email="test1@test.nl")
    user_2, token_2 = data_fixture.create_user_and_token(email="test2@test.nl")
    user_3, token_3 = data_fixture.create_user_and_token(email="test3@test.nl")
    group_1 = data_fixture.create_group()
    data_fixture.create_user_group(group=group_1, user=user_1, permissions="ADMIN")
    group_user = data_fixture.create_user_group(
        group=group_1, user=user_2, permissions="MEMBER"
    )

    response = api_client.patch(
        reverse("api:groups:users:item", kwargs={"group_user_id": 99999}),
        {"permissions": "MEMBER"},
        HTTP_AUTHORIZATION=f"JWT {token_1}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response_json["error"] == "ERROR_GROUP_USER_DOES_NOT_EXIST"

    response = api_client.patch(
        reverse("api:groups:users:item", kwargs={"group_user_id": group_user.id}),
        {"permissions": "ADMIN"},
        HTTP_AUTHORIZATION=f"JWT {token_3}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "ERROR_USER_NOT_IN_GROUP"

    response = api_client.patch(
        reverse("api:groups:users:item", kwargs={"group_user_id": group_user.id}),
        {"permissions": "ADMIN"},
        HTTP_AUTHORIZATION=f"JWT {token_2}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "ERROR_USER_INVALID_GROUP_PERMISSIONS"

    response = api_client.patch(
        reverse("api:groups:users:item", kwargs={"group_user_id": group_user.id}),
        {"permissions": "NOT_EXISTING"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token_1}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "ERROR_REQUEST_BODY_VALIDATION"
    assert response_json["detail"]["permissions"][0]["code"] == "invalid_choice"

    response = api_client.patch(
        reverse("api:groups:users:item", kwargs={"group_user_id": group_user.id}),
        {"permissions": "ADMIN"},
        HTTP_AUTHORIZATION=f"JWT {token_1}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["permissions"] == "ADMIN"


@pytest.mark.django_db
def test_delete_group_user(api_client, data_fixture):
    user_1, token_1 = data_fixture.create_user_and_token(email="test1@test.nl")
    user_2, token_2 = data_fixture.create_user_and_token(email="test2@test.nl")
    user_3, token_3 = data_fixture.create_user_and_token(email="test3@test.nl")
    group_1 = data_fixture.create_group()
    data_fixture.create_user_group(group=group_1, user=user_1, permissions="ADMIN")
    group_user = data_fixture.create_user_group(
        group=group_1, user=user_2, permissions="MEMBER"
    )

    response = api_client.delete(
        reverse("api:groups:users:item", kwargs={"group_user_id": 99999}),
        HTTP_AUTHORIZATION=f"JWT {token_1}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response_json["error"] == "ERROR_GROUP_USER_DOES_NOT_EXIST"

    response = api_client.delete(
        reverse("api:groups:users:item", kwargs={"group_user_id": group_user.id}),
        HTTP_AUTHORIZATION=f"JWT {token_3}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "ERROR_USER_NOT_IN_GROUP"

    response = api_client.delete(
        reverse("api:groups:users:item", kwargs={"group_user_id": group_user.id}),
        HTTP_AUTHORIZATION=f"JWT {token_2}",
    )
    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "ERROR_USER_INVALID_GROUP_PERMISSIONS"

    response = api_client.delete(
        reverse("api:groups:users:item", kwargs={"group_user_id": group_user.id}),
        HTTP_AUTHORIZATION=f"JWT {token_1}",
    )
    assert response.status_code == HTTP_204_NO_CONTENT
    assert GroupUser.objects.all().count() == 1
