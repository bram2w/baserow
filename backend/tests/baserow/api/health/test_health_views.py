from django.urls import reverse

import pytest
from health_check.backends import BaseHealthCheckBackend
from health_check.db.backends import DatabaseBackend
from health_check.exceptions import ServiceUnavailable
from health_check.plugins import plugin_dir
from rest_framework.status import HTTP_200_OK, HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN


class AlwaysFailingHealthCheck(BaseHealthCheckBackend):
    def check_status(self):
        raise ServiceUnavailable("Error")


@pytest.fixture(autouse=True)
def reset_health_checks_to_expected():
    plugin_dir.reset()
    plugin_dir.register(DatabaseBackend)


@pytest.mark.django_db
def test_anonymous_user_cant_get_full_health_checks(data_fixture, api_client):
    response = api_client.get(
        reverse("api:health:full_health_check"),
        content_type="application/json",
    )
    assert response.status_code == HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_non_staff_user_cant_get_full_health_checks(data_fixture, api_client):
    user, token = data_fixture.create_user_and_token()

    response = api_client.get(
        reverse("api:health:full_health_check"),
        content_type="application/json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_staff_user_can_get_full_health_checks(data_fixture, api_client):
    user, token = data_fixture.create_user_and_token(is_staff=True)

    response = api_client.get(
        reverse("api:health:full_health_check"),
        content_type="application/json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_200_OK


@pytest.mark.django_db
def test_full_health_check_endpoint_returns_dict_of_checks_vs_status_with_200_status(
    data_fixture, api_client
):
    user, token = data_fixture.create_user_and_token(is_staff=True)

    response = api_client.get(
        reverse("api:health:full_health_check"),
        content_type="application/json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_200_OK
    assert response.json() == {
        "passing": True,
        "checks": {
            "DatabaseBackend": "working",
        },
    }


@pytest.mark.django_db
def test_passing_is_false_when_one_critical_service_fails(data_fixture, api_client):
    user, token = data_fixture.create_user_and_token(is_staff=True)

    plugin_dir.register(AlwaysFailingHealthCheck)

    response = api_client.get(
        reverse("api:health:full_health_check"),
        content_type="application/json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_200_OK
    assert response.json() == {
        "checks": {
            "AlwaysFailingHealthCheck": "unavailable: Error",
            "DatabaseBackend": "working",
        },
        "passing": False,
    }
