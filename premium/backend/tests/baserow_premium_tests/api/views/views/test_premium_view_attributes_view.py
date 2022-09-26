from django.test.utils import override_settings

import pytest
from rest_framework.reverse import reverse
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_400_BAD_REQUEST,
    HTTP_402_PAYMENT_REQUIRED,
)


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_premium_view_attributes_view(api_client, premium_data_fixture):
    user, token = premium_data_fixture.create_user_and_token(
        email="test@test.nl",
        password="password",
        first_name="Test1",
        has_active_premium_license=True,
    )
    table = premium_data_fixture.create_database_table(user=user)
    view = premium_data_fixture.create_grid_view(table=table)

    response = api_client.patch(
        reverse(
            "api:premium:view:premium_view_attributes", kwargs={"view_id": view.id}
        ),
        data={"show_logo": False},
        format="json",
        **{"HTTP_AUTHORIZATION": f"JWT {token}"},
    )

    assert response.status_code == HTTP_200_OK
    assert response.json()["show_logo"] is False


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_premium_view_attributes_as_non_premium_user(api_client, premium_data_fixture):
    user, token = premium_data_fixture.create_user_and_token(
        has_active_premium_license=False
    )
    group = premium_data_fixture.create_group(user=user)
    database = premium_data_fixture.create_database_application(group=group)
    table = premium_data_fixture.create_database_table(database=database)
    view = premium_data_fixture.create_grid_view(table=table)

    response = api_client.patch(
        reverse(
            "api:premium:view:premium_view_attributes", kwargs={"view_id": view.id}
        ),
        {"show_logo": False},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    assert response.status_code == HTTP_402_PAYMENT_REQUIRED


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_premium_view_attributes_invalid_attributes(api_client, premium_data_fixture):
    user, token = premium_data_fixture.create_user_and_token(
        has_active_premium_license=True
    )
    group = premium_data_fixture.create_group(user=user)
    database = premium_data_fixture.create_database_application(group=group)
    table = premium_data_fixture.create_database_table(database=database)
    view = premium_data_fixture.create_grid_view(table=table, name="some name")

    response = api_client.patch(
        reverse(
            "api:premium:view:premium_view_attributes", kwargs={"view_id": view.id}
        ),
        {"name": "some new name"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    assert response.status_code == HTTP_200_OK
    assert response.json()["name"] == "some name"


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_premium_view_attributes_template(api_client, premium_data_fixture):
    user, token = premium_data_fixture.create_user_and_token(
        has_active_premium_license=True
    )
    group = premium_data_fixture.create_group(user=user)
    database = premium_data_fixture.create_database_application(group=group)
    table = premium_data_fixture.create_database_table(database=database)
    view = premium_data_fixture.create_grid_view(table=table, name="some name")
    premium_data_fixture.create_template(group=group)

    response = api_client.patch(
        reverse(
            "api:premium:view:premium_view_attributes", kwargs={"view_id": view.id}
        ),
        {"name": "some new name"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    assert response.status_code == HTTP_400_BAD_REQUEST
    assert (
        response.json()["error"] == "ERROR_CANNOT_UPDATE_PREMIUM_ATTRIBUTES_ON_TEMPLATE"
    )
