from django.urls import reverse

import pytest
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_404_NOT_FOUND,
)

from baserow.core.user_sources.models import UserSource


@pytest.mark.django_db
def test_get_user_sources(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    workspace = data_fixture.create_workspace(user=user)
    application = data_fixture.create_builder_application(workspace=workspace)
    database = data_fixture.create_database_application(workspace=workspace)
    data_fixture.create_database_table(database=database)
    user_source1 = data_fixture.create_user_source_with_first_type(
        application=application
    )
    user_source2 = data_fixture.create_user_source_with_first_type(
        application=application
    )
    user_source3 = data_fixture.create_user_source_with_first_type(
        application=application
    )
    data_fixture.create_user_source_with_first_type()

    url = reverse("api:user_sources:list", kwargs={"application_id": application.id})
    response = api_client.get(
        url,
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert len(response_json) == 3
    assert response_json[0]["id"] == user_source1.id
    assert response_json[0]["type"] == "local_baserow"
    assert response_json[1]["id"] == user_source2.id
    assert response_json[1]["type"] == "local_baserow"
    assert response_json[2]["id"] == user_source3.id
    assert response_json[2]["type"] == "local_baserow"


@pytest.mark.django_db
def test_create_user_source(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    workspace = data_fixture.create_workspace(user=user)
    application = data_fixture.create_builder_application(workspace=workspace)
    database = data_fixture.create_database_application(workspace=workspace)
    data_fixture.create_database_table(database=database)

    url = reverse("api:user_sources:list", kwargs={"application_id": application.id})
    response = api_client.post(
        url,
        {"type": "local_baserow", "name": "test"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["type"] == "local_baserow"

    response = api_client.post(
        url,
        {
            "type": "local_baserow",
            "name": "test",
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    response_json = response.json()
    assert response.status_code == HTTP_200_OK


@pytest.mark.django_db
def test_create_user_source_permission_denied(
    api_client, data_fixture, stub_check_permissions
):
    user, token = data_fixture.create_user_and_token()
    application = data_fixture.create_builder_application(user=user)

    url = reverse("api:user_sources:list", kwargs={"application_id": application.id})
    with stub_check_permissions(raise_permission_denied=True):
        response = api_client.post(
            url,
            {"type": "local_baserow", "name": "test"},
            format="json",
            HTTP_AUTHORIZATION=f"JWT {token}",
        )

    assert response.status_code == HTTP_401_UNAUTHORIZED
    assert response.json()["error"] == "PERMISSION_DENIED"


@pytest.mark.django_db
def test_create_user_source_application_does_not_exist(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()

    url = reverse("api:user_sources:list", kwargs={"application_id": 0})
    response = api_client.post(
        url,
        {"type": "local_baserow", "name": "test"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_APPLICATION_DOES_NOT_EXIST"


@pytest.mark.django_db
def test_create_user_source_bad_application_type(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    application = data_fixture.create_database_application(user=user)

    url = reverse("api:user_sources:list", kwargs={"application_id": application.id})
    response = api_client.post(
        url,
        {"type": "local_baserow", "name": "test"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_APPLICATION_OPERATION_NOT_SUPPORTED"


@pytest.mark.django_db
def test_update_user_source(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    application = data_fixture.create_builder_application(user=user)
    user_source1 = data_fixture.create_user_source_with_first_type(
        application=application
    )
    integration = data_fixture.create_local_baserow_integration(user=user)

    url = reverse("api:user_sources:item", kwargs={"user_source_id": user_source1.id})
    response = api_client.patch(
        url,
        {"integration_id": integration.id, "name": "newName"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    assert response.status_code == HTTP_200_OK
    assert response.json()["name"] == "newName"
    assert response.json()["integration_id"] == integration.id


@pytest.mark.django_db
@pytest.mark.skip  # No modifiable user_source yet
def test_update_user_source_bad_request(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    application = data_fixture.create_builder_application(user=user)
    user_source1 = data_fixture.create_user_source_with_first_type(
        application=application
    )

    url = reverse("api:user_sources:item", kwargs={"user_source_id": user_source1.id})
    response = api_client.patch(
        url,
        {"modifiable_field": []},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_REQUEST_BODY_VALIDATION"


@pytest.mark.django_db
def test_update_user_source_does_not_exist(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()

    url = reverse("api:user_sources:item", kwargs={"user_source_id": 0})
    response = api_client.patch(
        url,
        {"value": "test"},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_USER_SOURCE_DOES_NOT_EXIST"


@pytest.mark.django_db
def test_move_user_source_empty_payload(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    application = data_fixture.create_builder_application(user=user)
    user_source1 = data_fixture.create_user_source_with_first_type(
        application=application
    )
    user_source2 = data_fixture.create_user_source_with_first_type(
        application=application
    )
    user_source3 = data_fixture.create_user_source_with_first_type(
        application=application
    )

    url = reverse("api:user_sources:move", kwargs={"user_source_id": user_source1.id})
    response = api_client.patch(
        url,
        {},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_200_OK

    assert UserSource.objects.last().id == user_source1.id


@pytest.mark.django_db
def test_move_user_source_null_before_id(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    application = data_fixture.create_builder_application(user=user)
    user_source1 = data_fixture.create_user_source_with_first_type(
        application=application
    )
    user_source2 = data_fixture.create_user_source_with_first_type(
        application=application
    )
    user_source3 = data_fixture.create_user_source_with_first_type(
        application=application
    )

    url = reverse("api:user_sources:move", kwargs={"user_source_id": user_source1.id})
    response = api_client.patch(
        url,
        {"before_id": None},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_200_OK

    assert UserSource.objects.last().id == user_source1.id


@pytest.mark.django_db
def test_move_user_source_before(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    application = data_fixture.create_builder_application(user=user)
    user_source1 = data_fixture.create_user_source_with_first_type(
        application=application
    )
    user_source2 = data_fixture.create_user_source_with_first_type(
        application=application
    )
    user_source3 = data_fixture.create_user_source_with_first_type(
        application=application
    )

    url = reverse("api:user_sources:move", kwargs={"user_source_id": user_source3.id})
    response = api_client.patch(
        url,
        {"before_id": user_source2.id},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_200_OK
    assert response.json()["id"] == user_source3.id

    assert list(UserSource.objects.all())[1].id == user_source3.id


@pytest.mark.django_db
def test_move_user_source_before_not_in_same_application(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    application = data_fixture.create_builder_application(user=user)
    application2 = data_fixture.create_builder_application(user=user)
    user_source1 = data_fixture.create_user_source_with_first_type(
        application=application
    )
    user_source2 = data_fixture.create_user_source_with_first_type(
        application=application
    )
    user_source3 = data_fixture.create_user_source_with_first_type(
        application=application2
    )

    url = reverse("api:user_sources:move", kwargs={"user_source_id": user_source3.id})
    response = api_client.patch(
        url,
        {"before_id": user_source2.id},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_USER_SOURCE_NOT_IN_SAME_APPLICATION"


@pytest.mark.django_db
def test_move_user_source_bad_before_id(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    application = data_fixture.create_builder_application(user=user)
    user_source1 = data_fixture.create_user_source_with_first_type(
        application=application
    )

    url = reverse("api:user_sources:move", kwargs={"user_source_id": user_source1.id})
    response = api_client.patch(
        url,
        {"before_id": 9999},
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_delete_user_source(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    application = data_fixture.create_builder_application(user=user)
    user_source1 = data_fixture.create_user_source_with_first_type(
        application=application
    )

    url = reverse("api:user_sources:item", kwargs={"user_source_id": user_source1.id})
    response = api_client.delete(
        url,
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_204_NO_CONTENT


@pytest.mark.django_db
def test_delete_user_source_permission_denied(
    api_client, data_fixture, stub_check_permissions
):
    user, token = data_fixture.create_user_and_token()
    application = data_fixture.create_builder_application(user=user)
    user_source1 = data_fixture.create_user_source_with_first_type(
        application=application
    )

    url = reverse("api:user_sources:item", kwargs={"user_source_id": user_source1.id})

    with stub_check_permissions(raise_permission_denied=True):
        response = api_client.delete(
            url,
            format="json",
            HTTP_AUTHORIZATION=f"JWT {token}",
        )

    assert response.status_code == HTTP_401_UNAUTHORIZED
    assert response.json()["error"] == "PERMISSION_DENIED"


@pytest.mark.django_db
def test_delete_user_source_user_source_not_exist(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()

    url = reverse("api:user_sources:item", kwargs={"user_source_id": 0})
    response = api_client.delete(
        url,
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_USER_SOURCE_DOES_NOT_EXIST"
