from django.urls import reverse

import pytest
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST

from baserow.contrib.database.fields.handler import FieldHandler
from baserow.core.user_sources.exceptions import UserSourceImproperlyConfigured
from baserow.core.user_sources.registries import user_source_type_registry
from baserow.core.user_sources.service import UserSourceService
from baserow_enterprise.integrations.local_baserow.models import (
    LocalBaserowPasswordAppAuthProvider,
)

from .helpers import populate_local_baserow_test_data


@pytest.fixture(autouse=True)
def enable_enterprise_for_all_tests_here(enable_enterprise):
    pass


@pytest.mark.django_db
def test_create_local_baserow_password_app_auth_provider_w_field(
    data_fixture, api_client
):
    user, token = data_fixture.create_user_and_token()
    workspace = data_fixture.create_workspace(user=user)
    application = data_fixture.create_builder_application(workspace=workspace)
    database = data_fixture.create_database_application(workspace=workspace)

    integration = data_fixture.create_local_baserow_integration(application=application)

    table, fields, rows = data_fixture.build_table(
        user=user,
        database=database,
        columns=[
            ("Email", "text"),
            ("Name", "text"),
            ("Password", "password"),
        ],
        rows=[
            ["test@baserow.io", "Test", "password"],
        ],
    )

    email_field, name_field, password_field = fields

    url = reverse("api:user_sources:list", kwargs={"application_id": application.id})
    response = api_client.post(
        url,
        {
            "type": "local_baserow",
            "name": "test",
            "integration_id": integration.id,
            "table_id": table.id,
            "email_field_id": email_field.id,
            "name_field_id": name_field.id,
            "auth_providers": [
                {
                    "type": "local_baserow_password",
                    "domain": None,
                    "enabled": True,
                    "password_field_id": password_field.id,
                }
            ],
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    created = LocalBaserowPasswordAppAuthProvider.objects.first()

    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["auth_providers"] == [
        {
            "type": "local_baserow_password",
            "id": created.id,
            "domain": None,
            "password_field_id": password_field.id,
        }
    ]


@pytest.mark.django_db
def test_create_local_baserow_password_app_auth_provider_w_wrong_field_type(
    data_fixture, api_client
):
    user, token = data_fixture.create_user_and_token()
    workspace = data_fixture.create_workspace(user=user)
    application = data_fixture.create_builder_application(workspace=workspace)
    database = data_fixture.create_database_application(workspace=workspace)

    integration = data_fixture.create_local_baserow_integration(application=application)

    table, fields, rows = data_fixture.build_table(
        user=user,
        database=database,
        columns=[
            ("Email", "text"),
            ("Name", "text"),
            ("Password", "url"),
        ],
        rows=[
            ["test@baserow.io", "Test", "password"],
        ],
    )

    email_field, name_field, password_field = fields

    url = reverse("api:user_sources:list", kwargs={"application_id": application.id})
    response = api_client.post(
        url,
        {
            "type": "local_baserow",
            "name": "test",
            "integration_id": integration.id,
            "table_id": table.id,
            "email_field_id": email_field.id,
            "name_field_id": name_field.id,
            "auth_providers": [
                {
                    "type": "local_baserow_password",
                    "domain": None,
                    "enabled": True,
                    "password_field_id": password_field.id,
                }
            ],
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "ERROR_REQUEST_BODY_VALIDATION"
    assert response_json["detail"]["password_field_id"][0]["code"] == "invalid_field"


@pytest.mark.django_db
def test_create_local_baserow_password_app_auth_provider_w_wrong_field_id(
    data_fixture, api_client
):
    user, token = data_fixture.create_user_and_token()
    workspace = data_fixture.create_workspace(user=user)
    application = data_fixture.create_builder_application(workspace=workspace)
    database = data_fixture.create_database_application(workspace=workspace)

    integration = data_fixture.create_local_baserow_integration(application=application)

    table, fields, rows = data_fixture.build_table(
        user=user,
        database=database,
        columns=[
            ("Email", "text"),
            ("Name", "text"),
            ("Password", "text"),
        ],
        rows=[
            ["test@baserow.io", "Test", "password"],
        ],
    )

    email_field, name_field, password_field = fields

    url = reverse("api:user_sources:list", kwargs={"application_id": application.id})
    response = api_client.post(
        url,
        {
            "type": "local_baserow",
            "name": "test",
            "integration_id": integration.id,
            "table_id": table.id,
            "email_field_id": email_field.id,
            "name_field_id": name_field.id,
            "auth_providers": [
                {
                    "type": "local_baserow_password",
                    "domain": None,
                    "enabled": True,
                    "password_field_id": 0,
                }
            ],
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "ERROR_REQUEST_BODY_VALIDATION"
    assert response_json["detail"]["password_field_id"][0]["code"] == "invalid_field"

    FieldHandler().delete_field(user, password_field)

    response = api_client.post(
        url,
        {
            "type": "local_baserow",
            "name": "test",
            "integration_id": integration.id,
            "table_id": table.id,
            "email_field_id": email_field.id,
            "name_field_id": name_field.id,
            "auth_providers": [
                {
                    "type": "local_baserow_password",
                    "domain": None,
                    "enabled": True,
                    "password_field_id": password_field.id,
                }
            ],
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    response_json = response.json()
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response_json["error"] == "ERROR_REQUEST_BODY_VALIDATION"
    assert response_json["detail"]["password_field_id"][0]["code"] == "invalid_field"


@pytest.mark.django_db
def test_local_baserow_password_app_auth_provider_after_user_source_update(
    data_fixture,
):
    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=user)
    application = data_fixture.create_builder_application(workspace=workspace)
    database = data_fixture.create_database_application(workspace=workspace)
    data_fixture.create_database_table(database=database)
    integration = data_fixture.create_local_baserow_integration(application=application)

    table, fields, rows = data_fixture.build_table(
        user=user,
        columns=[
            ("Email", "text"),
            ("Name", "text"),
            ("Password", "text"),
        ],
        rows=[
            ["test@baserow.io", "Test", "super not secret"],
        ],
    )

    email_field, name_field, password_field = fields

    table2, fields2, rows2 = data_fixture.build_table(
        user=user,
        columns=[
            ("Email", "text"),
            ("Name", "text"),
            ("Password", "text"),
        ],
        rows=[
            ["test@baserow.io", "Test", "super not secret"],
        ],
    )

    local_baserow_user_source_type = user_source_type_registry.get("local_baserow")

    user_source = data_fixture.create_user_source(
        local_baserow_user_source_type.model_class,
        application=application,
        integration=integration,
        table=table,
        email_field=email_field,
        name_field=name_field,
    )

    app_auth_provider = data_fixture.create_app_auth_provider(
        LocalBaserowPasswordAppAuthProvider,
        user_source=user_source,
        password_field=password_field,
    )

    UserSourceService().update_user_source(user, user_source, table=table2)

    app_auth_provider.refresh_from_db()

    assert app_auth_provider.password_field_id is None


@pytest.mark.django_db
def test_local_baserow_token_auth(api_client, data_fixture):
    data = populate_local_baserow_test_data(data_fixture)

    response = api_client.post(
        reverse(
            "api:user_sources:token_auth",
            kwargs={"user_source_id": data["user_source"].id},
        ),
        {"email": "test@baserow.io", "password": "super not secret"},
        format="json",
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK

    assert "refresh_token" in response_json
    assert "access_token" in response_json


@pytest.mark.django_db
def test_local_baserow_user_source_authentication_improperly_configured(
    data_fixture,
):
    data = populate_local_baserow_test_data(data_fixture)

    user_source = data["user_source"]
    user_source_type = user_source.get_type()

    data["auth_provider"].password_field = None
    data["auth_provider"].save()

    with pytest.raises(UserSourceImproperlyConfigured):
        user_source_type.authenticate(
            user_source, email="test@baserow.io", password="super not secret"
        )
