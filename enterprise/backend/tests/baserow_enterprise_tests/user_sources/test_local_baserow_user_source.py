from collections import defaultdict

from django.urls import reverse

import pytest
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST

from baserow.core.user_sources.handler import UserSourceHandler
from baserow.core.user_sources.registries import user_source_type_registry
from baserow.core.utils import MirrorDict


@pytest.fixture(autouse=True)
def enable_enterprise_for_all_tests_here(enable_enterprise):
    pass


@pytest.mark.django_db
def test_get_user_sources(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
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
        ],
        rows=[
            ["test@baserow.io", "Test"],
        ],
    )

    email_field, name_field = fields

    local_baserow_user_source_type = user_source_type_registry.get("local_baserow")

    user_source1 = data_fixture.create_user_source(
        local_baserow_user_source_type.model_class,
        application=application,
        integration=integration,
        table=table,
        email_field=email_field,
        name_field=name_field,
    )

    user_source2 = data_fixture.create_user_source(
        local_baserow_user_source_type.model_class,
        application=application,
        integration=integration,
        table=table,
        email_field=email_field,
    )

    user_source3 = data_fixture.create_user_source(
        local_baserow_user_source_type.model_class,
        application=application,
        integration=integration,
        table=table,
    )

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
    assert response_json[0]["integration_id"] == integration.id
    assert response_json[0]["table_id"] == table.id
    assert response_json[0]["email_field_id"] == email_field.id
    assert response_json[0]["name_field_id"] == name_field.id

    assert response_json[1]["id"] == user_source2.id
    assert response_json[1]["type"] == "local_baserow"
    assert response_json[1]["integration_id"] == integration.id
    assert response_json[1]["table_id"] == table.id
    assert response_json[1]["email_field_id"] == email_field.id
    assert response_json[1]["name_field_id"] is None

    assert response_json[2]["id"] == user_source3.id
    assert response_json[2]["type"] == "local_baserow"
    assert response_json[2]["integration_id"] == integration.id
    assert response_json[2]["table_id"] == table.id
    assert response_json[2]["email_field_id"] is None
    assert response_json[2]["name_field_id"] is None


@pytest.mark.django_db
def test_create_local_baserow_user_source(api_client, data_fixture):
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
        ],
        rows=[
            ["test@baserow.io", "Test"],
        ],
    )

    email_field, name_field = fields

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
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["type"] == "local_baserow"
    assert response_json["integration_id"] == integration.id
    assert response_json["table_id"] == table.id
    assert response_json["email_field_id"] == email_field.id
    assert response_json["name_field_id"] == name_field.id


@pytest.mark.django_db
def test_create_user_source_table_from_other_workspace(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    workspace = data_fixture.create_workspace(user=user)
    application = data_fixture.create_builder_application(workspace=workspace)
    database = data_fixture.create_database_application(workspace=workspace)

    integration = data_fixture.create_local_baserow_integration(
        application=application, user=user
    )

    table_from_other_workspace, fields, rows = data_fixture.build_table(
        user=user,
        columns=[
            ("Email", "text"),
            ("Name", "text"),
        ],
        rows=[
            ["test@baserow.io", "Test"],
        ],
    )

    url = reverse("api:user_sources:list", kwargs={"application_id": application.id})
    response = api_client.post(
        url,
        {
            "type": "local_baserow",
            "name": "test",
            "integration_id": integration.id,
            "table_id": table_from_other_workspace.id,
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_REQUEST_BODY_VALIDATION"
    assert response.json()["detail"]["table_id"][0]["code"] == "invalid_table"

    response = api_client.post(
        url,
        {
            "type": "local_baserow",
            "name": "test",
            "table_id": table_from_other_workspace.id,
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_REQUEST_BODY_VALIDATION"
    assert response.json()["detail"]["table_id"][0]["code"] == "invalid_table"


@pytest.mark.django_db
def test_create_user_source_field_from_other_table(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    workspace = data_fixture.create_workspace(user=user)
    application = data_fixture.create_builder_application(workspace=workspace)
    database = data_fixture.create_database_application(workspace=workspace)

    integration = data_fixture.create_local_baserow_integration(
        application=application, user=user
    )

    table_from_same_workspace1, fields, rows = data_fixture.build_table(
        user=user,
        database=database,
        columns=[
            ("Email", "text"),
            ("Name", "text"),
        ],
        rows=[
            ["test@baserow.io", "Test"],
        ],
    )

    table_from_same_workspace2, fields2, rows = data_fixture.build_table(
        user=user,
        database=database,
        columns=[
            ("Email", "text"),
            ("Name", "text"),
        ],
        rows=[
            ["test@baserow.io", "Test"],
        ],
    )

    email_field_other_table, name_field_other_table = fields2

    url = reverse("api:user_sources:list", kwargs={"application_id": application.id})
    response = api_client.post(
        url,
        {
            "type": "local_baserow",
            "name": "test",
            "integration_id": integration.id,
            "table_id": table_from_same_workspace1.id,
            "email_field_id": email_field_other_table.id,
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_REQUEST_BODY_VALIDATION"
    assert response.json()["detail"]["email_field_id"][0]["code"] == "invalid_field"

    response = api_client.post(
        url,
        {
            "type": "local_baserow",
            "name": "test",
            "integration_id": integration.id,
            "table_id": table_from_same_workspace1.id,
            "name_field_id": name_field_other_table.id,
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_REQUEST_BODY_VALIDATION"
    assert response.json()["detail"]["name_field_id"][0]["code"] == "invalid_field"

    response = api_client.post(
        url,
        {
            "type": "local_baserow",
            "name": "test",
            "integration_id": integration.id,
            "name_field_id": name_field_other_table.id,
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_REQUEST_BODY_VALIDATION"
    assert response.json()["detail"]["name_field_id"][0]["code"] == "invalid_field"


@pytest.mark.django_db
def test_export_user_source(data_fixture):
    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=user)
    application = data_fixture.create_builder_application(workspace=workspace)
    database = data_fixture.create_database_application(workspace=workspace)

    integration = data_fixture.create_local_baserow_integration(
        application=application, user=user
    )

    table_from_same_workspace1, fields, rows = data_fixture.build_table(
        user=user,
        database=database,
        columns=[
            ("Email", "text"),
            ("Name", "text"),
        ],
        rows=[
            ["test@baserow.io", "Test"],
        ],
    )

    email_field, name_field = fields

    user_source = data_fixture.create_user_source_with_first_type(
        integration=integration,
        name="Test name",
        table=table_from_same_workspace1,
        email_field=email_field,
        name_field=name_field,
    )

    exported = UserSourceHandler().export_user_source(user_source)

    assert exported == {
        "email_field_id": email_field.id,
        "id": exported["id"],
        "integration_id": integration.id,
        "name": "Test name",
        "name_field_id": name_field.id,
        "order": "1.00000000000000000000",
        "table_id": table_from_same_workspace1.id,
        "type": "local_baserow",
    }


@pytest.mark.django_db
def test_import_local_baserow_user_source(data_fixture):
    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=user)
    application = data_fixture.create_builder_application(workspace=workspace)
    database = data_fixture.create_database_application(workspace=workspace)

    integration = data_fixture.create_local_baserow_integration(
        application=application, user=user
    )

    table_from_same_workspace1, fields, rows = data_fixture.build_table(
        user=user,
        database=database,
        columns=[
            ("Email", "text"),
            ("Name", "text"),
        ],
        rows=[
            ["test@baserow.io", "Test"],
        ],
    )

    email_field, name_field = fields

    TO_IMPORT = {
        "email_field_id": 42,
        "id": 28,
        "integration_id": 42,
        "name": "Test name",
        "name_field_id": 43,
        "order": "1.00000000000000000000",
        "table_id": 42,
        "type": "local_baserow",
    }

    id_mapping = defaultdict(MirrorDict)
    id_mapping["integrations"] = {42: integration.id}
    id_mapping["database_tables"] = {42: table_from_same_workspace1.id}
    id_mapping["database_fields"] = {42: email_field.id, 43: name_field.id}

    imported_instance = UserSourceHandler().import_user_source(
        application, TO_IMPORT, id_mapping
    )

    assert imported_instance.table_id == table_from_same_workspace1.id
    assert imported_instance.email_field_id == email_field.id
    assert imported_instance.name_field_id == name_field.id
