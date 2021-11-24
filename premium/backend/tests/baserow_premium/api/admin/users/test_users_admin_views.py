import json
import pytest

from django.shortcuts import reverse
from django.utils import timezone
from django.utils.datetime_safe import datetime
from django.test.utils import override_settings

from rest_framework.status import (
    HTTP_200_OK,
    HTTP_402_PAYMENT_REQUIRED,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
)

from baserow.core.models import (
    GROUP_USER_PERMISSION_MEMBER,
    GROUP_USER_PERMISSION_ADMIN,
)

invalid_passwords = [
    "a",
    "ab",
    "ask",
    "oiue",
    "dsj43",
    "984kds",
    "dsfkjh4",
]


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_non_admin_cannot_see_admin_users_endpoint(api_client, premium_data_fixture):
    non_staff_user, token = premium_data_fixture.create_user_and_token(
        email="test@test.nl",
        password="password",
        first_name="Test1",
        is_staff=False,
        has_active_premium_license=True,
    )
    response = api_client.get(
        reverse("api:premium:admin:users:list"),
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_403_FORBIDDEN


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_admin_can_see_admin_users_endpoint(api_client, premium_data_fixture):
    staff_user, token = premium_data_fixture.create_user_and_token(
        email="test@test.nl",
        password="password",
        first_name="Test1",
        is_staff=True,
        date_joined=datetime(2021, 4, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        has_active_premium_license=True,
    )
    group_user_is_admin_of = premium_data_fixture.create_group()
    premium_data_fixture.create_user_group(
        group=group_user_is_admin_of,
        user=staff_user,
        permissions=GROUP_USER_PERMISSION_ADMIN,
    )
    group_user_is_not_admin_of = premium_data_fixture.create_group()
    premium_data_fixture.create_user_group(
        group=group_user_is_not_admin_of,
        user=staff_user,
        permissions=GROUP_USER_PERMISSION_MEMBER,
    )
    response = api_client.get(
        reverse("api:premium:admin:users:list"),
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_200_OK
    assert response.json() == {
        "count": 1,
        "next": None,
        "previous": None,
        "results": [
            {
                "date_joined": "2021-04-01T01:00:00Z",
                "name": staff_user.first_name,
                "username": staff_user.email,
                "groups": [
                    {
                        "id": group_user_is_admin_of.id,
                        "name": group_user_is_admin_of.name,
                        "permissions": GROUP_USER_PERMISSION_ADMIN,
                    },
                    {
                        "id": group_user_is_not_admin_of.id,
                        "name": group_user_is_not_admin_of.name,
                        "permissions": GROUP_USER_PERMISSION_MEMBER,
                    },
                ],
                "id": staff_user.id,
                "is_staff": True,
                "is_active": True,
                "last_login": None,
            }
        ],
    }


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_admin_list_users_without_premium_license(api_client, premium_data_fixture):
    staff_user, token = premium_data_fixture.create_user_and_token(
        email="test@test.nl",
        password="password",
        first_name="Test1",
        is_staff=True,
        date_joined=datetime(2021, 4, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
    )
    response = api_client.get(
        reverse("api:premium:admin:users:list"),
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_402_PAYMENT_REQUIRED
    assert response.json()["error"] == "ERROR_NO_ACTIVE_PREMIUM_LICENSE"


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_admin_with_invalid_token_cannot_see_admin_users(
    api_client, premium_data_fixture
):
    premium_data_fixture.create_user_and_token(
        email="test@test.nl",
        password="password",
        first_name="Test1",
        is_staff=True,
        has_active_premium_license=True,
    )
    response = api_client.get(
        reverse("api:premium:admin:users:list"),
        format="json",
        HTTP_AUTHORIZATION=f"JWT abc123",
    )
    assert response.status_code == HTTP_401_UNAUTHORIZED
    assert response.json()["error"] == "ERROR_DECODING_SIGNATURE"


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_admin_accessing_invalid_user_admin_page_returns_error(
    api_client, premium_data_fixture
):
    _, token = premium_data_fixture.create_user_and_token(
        email="test@test.nl",
        password="password",
        first_name="Test1",
        is_staff=True,
        has_active_premium_license=True,
    )
    url = reverse("api:premium:admin:users:list")
    response = api_client.get(
        f"{url}?page=2",
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_INVALID_PAGE"


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_admin_accessing_user_admin_with_invalid_page_size_returns_error(
    api_client, premium_data_fixture
):
    _, token = premium_data_fixture.create_user_and_token(
        email="test@test.nl",
        password="password",
        first_name="Test1",
        is_staff=True,
        has_active_premium_license=True,
    )
    url = reverse("api:premium:admin:users:list")
    response = api_client.get(
        f"{url}?page=1&size=201",
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_PAGE_SIZE_LIMIT"


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_admin_can_search_users(api_client, premium_data_fixture):
    _, token = premium_data_fixture.create_user_and_token(
        email="test@test.nl",
        password="password",
        first_name="Test1",
        is_staff=True,
        has_active_premium_license=True,
    )
    searched_for_user = premium_data_fixture.create_user(
        email="specific_user@test.nl",
        password="password",
        first_name="Test1",
        date_joined=datetime(2021, 4, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        has_active_premium_license=True,
    )
    url = reverse("api:premium:admin:users:list")
    response = api_client.get(
        f"{url}?page=1&search=specific_user",
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_200_OK
    assert response.json() == {
        "count": 1,
        "next": None,
        "previous": None,
        "results": [
            {
                "date_joined": "2021-04-01T01:00:00Z",
                "name": searched_for_user.first_name,
                "username": searched_for_user.email,
                "groups": [],
                "id": searched_for_user.id,
                "is_staff": False,
                "is_active": True,
                "last_login": None,
            }
        ],
    }


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_admin_can_sort_users(api_client, premium_data_fixture):
    _, token = premium_data_fixture.create_user_and_token(
        email="test@test.nl",
        password="password",
        first_name="Test1",
        is_staff=True,
        has_active_premium_license=True,
    )
    searched_for_user = premium_data_fixture.create_user(
        email="specific_user@test.nl",
        password="password",
        first_name="Test1",
        date_joined=datetime(2021, 4, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        has_active_premium_license=True,
    )
    url = reverse("api:premium:admin:users:list")
    response = api_client.get(
        f"{url}?page=1&search=specific_user",
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_200_OK
    assert response.json() == {
        "count": 1,
        "next": None,
        "previous": None,
        "results": [
            {
                "date_joined": "2021-04-01T01:00:00Z",
                "name": searched_for_user.first_name,
                "username": searched_for_user.email,
                "groups": [],
                "id": searched_for_user.id,
                "is_staff": False,
                "is_active": True,
                "last_login": None,
            }
        ],
    }


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_returns_error_response_if_invalid_sort_field_provided(
    api_client, premium_data_fixture
):
    _, token = premium_data_fixture.create_user_and_token(
        email="test@test.nl",
        password="password",
        first_name="Test1",
        is_staff=True,
        has_active_premium_license=True,
    )
    url = reverse("api:premium:admin:users:list")
    response = api_client.get(
        f"{url}?page=1&sorts=-invalid_field_name",
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_ADMIN_LISTING_INVALID_SORT_ATTRIBUTE"


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_returns_error_response_if_sort_direction_not_provided(
    api_client, premium_data_fixture
):
    _, token = premium_data_fixture.create_user_and_token(
        email="test@test.nl",
        password="password",
        first_name="Test1",
        is_staff=True,
        has_active_premium_license=True,
    )
    url = reverse("api:premium:admin:users:list")
    response = api_client.get(
        f"{url}?page=1&sorts=username",
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_ADMIN_LISTING_INVALID_SORT_DIRECTION"


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_returns_error_response_if_invalid_sort_direction_provided(
    api_client, premium_data_fixture
):
    _, token = premium_data_fixture.create_user_and_token(
        email="test@test.nl",
        password="password",
        first_name="Test1",
        is_staff=True,
        has_active_premium_license=True,
    )
    url = reverse("api:premium:admin:users:list")
    response = api_client.get(
        f"{url}?page=1&sorts=*username",
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_ADMIN_LISTING_INVALID_SORT_DIRECTION"


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_returns_error_response_if_invalid_sorts_mixed_with_valid_ones(
    api_client, premium_data_fixture
):
    _, token = premium_data_fixture.create_user_and_token(
        email="test@test.nl",
        password="password",
        first_name="Test1",
        is_staff=True,
        has_active_premium_license=True,
    )
    url = reverse("api:premium:admin:users:list")
    response = api_client.get(
        f"{url}?page=1&sorts=+username,username,-invalid_field",
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_ADMIN_LISTING_INVALID_SORT_DIRECTION"


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_returns_error_response_if_blank_sorts_provided(
    api_client, premium_data_fixture
):
    _, token = premium_data_fixture.create_user_and_token(
        email="test@test.nl",
        password="password",
        first_name="Test1",
        is_staff=True,
        has_active_premium_license=True,
    )
    url = reverse("api:premium:admin:users:list")
    response = api_client.get(
        f"{url}?page=1&sorts=,,",
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_ADMIN_LISTING_INVALID_SORT_ATTRIBUTE"


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_returns_error_response_if_no_sorts_provided(api_client, premium_data_fixture):
    _, token = premium_data_fixture.create_user_and_token(
        email="test@test.nl",
        password="password",
        first_name="Test1",
        is_staff=True,
        has_active_premium_license=True,
    )
    url = reverse("api:premium:admin:users:list")
    response = api_client.get(
        f"{url}?page=1&sorts=",
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_ADMIN_LISTING_INVALID_SORT_ATTRIBUTE"


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_non_admin_cannot_delete_user(api_client, premium_data_fixture):
    _, non_admin_token = premium_data_fixture.create_user_and_token(
        email="test@test.nl",
        password="password",
        first_name="Test1",
        is_staff=False,
        has_active_premium_license=True,
    )
    user_to_delete = premium_data_fixture.create_user(
        email="specific_user@test.nl",
        password="password",
        first_name="Test1",
        has_active_premium_license=True,
    )
    url = reverse("api:premium:admin:users:edit", kwargs={"user_id": user_to_delete.id})
    response = api_client.delete(
        url,
        format="json",
        HTTP_AUTHORIZATION=f"JWT {non_admin_token}",
    )
    assert response.status_code == HTTP_403_FORBIDDEN


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_admin_cannot_delete_user_without_premium_license(
    api_client, premium_data_fixture
):
    _, admin_token = premium_data_fixture.create_user_and_token(
        email="test@test.nl",
        password="password",
        first_name="Test1",
        is_staff=True,
    )
    user_to_delete = premium_data_fixture.create_user(
        email="specific_user@test.nl",
        password="password",
        first_name="Test1",
    )
    url = reverse("api:premium:admin:users:edit", kwargs={"user_id": user_to_delete.id})
    response = api_client.delete(
        url,
        format="json",
        HTTP_AUTHORIZATION=f"JWT {admin_token}",
    )
    assert response.status_code == HTTP_402_PAYMENT_REQUIRED
    assert response.json()["error"] == "ERROR_NO_ACTIVE_PREMIUM_LICENSE"


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_admin_can_delete_user(api_client, premium_data_fixture):
    _, token = premium_data_fixture.create_user_and_token(
        email="test@test.nl",
        password="password",
        first_name="Test1",
        is_staff=True,
        has_active_premium_license=True,
    )
    user_to_delete = premium_data_fixture.create_user(
        email="specific_user@test.nl",
        password="password",
        first_name="Test1",
        has_active_premium_license=True,
    )
    url = reverse("api:premium:admin:users:edit", kwargs={"user_id": user_to_delete.id})
    response = api_client.delete(
        url,
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_204_NO_CONTENT

    response = api_client.get(
        reverse("api:premium:admin:users:list"),
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_200_OK
    assert response.json()["count"] == 1


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_non_admin_cannot_patch_user(api_client, premium_data_fixture):
    non_admin_user, non_admin_user_token = premium_data_fixture.create_user_and_token(
        email="test@test.nl",
        password="password",
        first_name="Test1",
        is_staff=False,
        has_active_premium_license=True,
    )
    url = reverse("api:premium:admin:users:edit", kwargs={"user_id": non_admin_user.id})
    response = api_client.patch(
        url,
        {"username": "some_other_email@test.nl"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {non_admin_user_token}",
    )
    assert response.status_code == HTTP_403_FORBIDDEN

    non_admin_user.refresh_from_db()
    assert non_admin_user.email == "test@test.nl"


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_non_admin_cannot_patch_user_without_premium_license(
    api_client, premium_data_fixture
):
    non_admin_user, non_admin_user_token = premium_data_fixture.create_user_and_token(
        email="test@test.nl",
        password="password",
        first_name="Test1",
        is_staff=True,
    )
    url = reverse("api:premium:admin:users:edit", kwargs={"user_id": non_admin_user.id})
    response = api_client.patch(
        url,
        {"username": "some_other_email@test.nl"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {non_admin_user_token}",
    )
    assert response.status_code == HTTP_402_PAYMENT_REQUIRED
    assert response.json()["error"] == "ERROR_NO_ACTIVE_PREMIUM_LICENSE"

    non_admin_user.refresh_from_db()
    assert non_admin_user.email == "test@test.nl"


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_admin_can_patch_user(api_client, premium_data_fixture):
    user, token = premium_data_fixture.create_user_and_token(
        email="test@test.nl",
        password="password",
        first_name="Test1",
        is_staff=True,
        date_joined=datetime(2021, 4, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        has_active_premium_license=True,
    )
    url = reverse("api:premium:admin:users:edit", kwargs={"user_id": user.id})
    old_password = user.password
    response = api_client.patch(
        url,
        {"username": "some_other_email@test.nl", "password": "new_password"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    user.refresh_from_db()
    assert user.password != old_password
    assert response.status_code == HTTP_200_OK
    assert response.json() == {
        "date_joined": "2021-04-01T01:00:00Z",
        "name": user.first_name,
        "username": "some_other_email@test.nl",
        "groups": [],
        "id": user.id,
        "is_staff": True,
        "is_active": True,
        "last_login": None,
    }


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_admin_can_patch_user_without_providing_password(
    api_client, premium_data_fixture
):
    user, token = premium_data_fixture.create_user_and_token(
        email="test@test.nl",
        password="password",
        first_name="Test1",
        is_staff=True,
        date_joined=datetime(2021, 4, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        has_active_premium_license=True,
    )
    url = reverse("api:premium:admin:users:edit", kwargs={"user_id": user.id})
    old_password = user.password
    response = api_client.patch(
        url,
        {"username": "some_other_email@test.nl", "name": "Test2"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    user.refresh_from_db()
    assert user.password == old_password
    assert response.status_code == HTTP_200_OK
    assert response.json() == {
        "date_joined": "2021-04-01T01:00:00Z",
        "name": "Test2",
        "username": "some_other_email@test.nl",
        "groups": [],
        "id": user.id,
        "is_staff": True,
        "is_active": True,
        "last_login": None,
    }


@pytest.mark.django_db
@override_settings(DEBUG=True)
@pytest.mark.parametrize("invalid_password", invalid_passwords)
def test_invalid_password_returns_400(
    api_client, premium_data_fixture, invalid_password
):
    user, token = premium_data_fixture.create_user_and_token(
        email="test@test.nl",
        password="password",
        first_name="Test1",
        is_staff=True,
        date_joined=datetime(2021, 4, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        has_active_premium_license=True,
    )

    user_to_edit = premium_data_fixture.create_user(
        email="second@test.nl",
        password="password",
        first_name="Test1",
        is_staff=False,
    )
    url = reverse("api:premium:admin:users:edit", kwargs={"user_id": user_to_edit.id})

    response = api_client.patch(
        url,
        {"username": user_to_edit.email, "password": invalid_password},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_REQUEST_BODY_VALIDATION"
    assert (
        response.json()["detail"]["password"][0]["code"] == "password_validation_failed"
    )

    # just sending the password will throw the same error
    response = api_client.patch(
        url,
        {"password": invalid_password},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_REQUEST_BODY_VALIDATION"
    assert (
        response.json()["detail"]["password"][0]["code"] == "password_validation_failed"
    )


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_error_returned_when_invalid_field_supplied_to_edit(
    api_client, premium_data_fixture
):
    user, token = premium_data_fixture.create_user_and_token(
        email="test@test.nl",
        password="password",
        first_name="Test1",
        is_staff=True,
        date_joined=datetime(2021, 4, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        has_active_premium_license=True,
    )
    url = reverse("api:premium:admin:users:edit", kwargs={"user_id": user.id})

    # We have to provide a str as otherwise the test api client will "helpfully" try
    # to serialize the dict using the endpoints serializer, which will fail before
    # actually running the endpoint.
    response = api_client.patch(
        url,
        json.dumps({"date_joined": "2021-04-01T01:00:00Z"}),
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_REQUEST_BODY_VALIDATION"


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_error_returned_when_updating_user_with_invalid_email(
    api_client, premium_data_fixture
):
    user, token = premium_data_fixture.create_user_and_token(
        email="test@test.nl",
        password="password",
        first_name="Test1",
        is_staff=True,
        date_joined=datetime(2021, 4, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        has_active_premium_license=True,
    )
    url = reverse("api:premium:admin:users:edit", kwargs={"user_id": user.id})

    # We have to provide a str as otherwise the test api client will "helpfully" try
    # to serialize the dict using the endpoints serializer, which will fail before
    # actually running the endpoint.
    response = api_client.patch(
        url,
        json.dumps({"username": "invalid email address"}),
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_REQUEST_BODY_VALIDATION"


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_error_returned_when_valid_and_invalid_fields_supplied_to_edit(
    api_client, premium_data_fixture
):
    user, token = premium_data_fixture.create_user_and_token(
        email="test@test.nl",
        password="password",
        first_name="Test1",
        is_staff=True,
        date_joined=datetime(2021, 4, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        has_active_premium_license=True,
    )
    url = reverse("api:premium:admin:users:edit", kwargs={"user_id": user.id})

    # We have to provide a str as otherwise the test api client will "helpfully" try
    # to serialize the dict using the endpoints serializer, which will fail before
    # actually running the endpoint.
    response = api_client.patch(
        url,
        json.dumps({"is_active": False, "date_joined": "2021-04-01T01:00:00Z"}),
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_REQUEST_BODY_VALIDATION"


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_admin_getting_view_users_only_runs_two_queries_instead_of_n(
    premium_data_fixture, django_assert_num_queries, api_client
):
    _, token = premium_data_fixture.create_user_and_token(
        email="test@test.nl",
        password="password",
        first_name="Test1",
        is_staff=True,
        has_active_premium_license=True,
    )
    fixed_num_of_queries_unrelated_to_number_of_rows = 6

    for i in range(10):
        premium_data_fixture.create_user_group()

    with django_assert_num_queries(fixed_num_of_queries_unrelated_to_number_of_rows):
        response = api_client.get(
            reverse("api:premium:admin:users:list"),
            format="json",
            HTTP_AUTHORIZATION=f"JWT {token}",
        )
    assert response.status_code == HTTP_200_OK
    assert response.json()["count"] == 11

    # Make even more to ensure that more rows don't result in more queries.
    for i in range(10):
        premium_data_fixture.create_user_group()

    with django_assert_num_queries(fixed_num_of_queries_unrelated_to_number_of_rows):
        response = api_client.get(
            reverse("api:premium:admin:users:list"),
            format="json",
            HTTP_AUTHORIZATION=f"JWT {token}",
        )
    assert response.status_code == HTTP_200_OK
    assert response.json()["count"] == 21
