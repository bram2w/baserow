from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

import pytest
from rest_framework.status import HTTP_200_OK

from baserow.contrib.integrations.local_baserow.integration_types import (
    LocalBaserowIntegrationType,
)
from baserow.core.integrations.registries import integration_type_registry
from baserow.core.integrations.service import IntegrationService


@pytest.mark.django_db
def test_create_local_baserow_integration_with_user(data_fixture):
    user = data_fixture.create_user()
    application = data_fixture.create_builder_application(user=user)

    integration_type = integration_type_registry.get("local_baserow")

    integration = IntegrationService().create_integration(
        user, integration_type, application=application
    )

    assert integration.authorized_user.id == user.id


@pytest.mark.django_db
def test_get_local_baserow_databases_no_databases(data_fixture):
    user = data_fixture.create_user()
    integration = data_fixture.create_local_baserow_integration(authorized_user=user)

    databases = LocalBaserowIntegrationType.get_local_baserow_databases(integration)

    assert len(databases) == 0


@pytest.mark.django_db
def test_get_local_baserow_databases(data_fixture):
    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=user)
    builder = data_fixture.create_builder_application(workspace=workspace)
    integration = data_fixture.create_local_baserow_integration(
        authorized_user=user, application=builder
    )
    database = data_fixture.create_database_application(
        user=user, workspace=workspace, order=1
    )
    database_2 = data_fixture.create_database_application(
        user=user, workspace=workspace, order=2
    )
    table = data_fixture.create_database_table(database=database, order=1)
    table_2 = data_fixture.create_database_table(database=database_2, order=1)
    table_3 = data_fixture.create_database_table(database=database_2, order=2)

    # Create some unrelated database and tables, that should not be included in the
    # result.
    database_tmp_2 = data_fixture.create_database_application(user=user)
    database_tmp_3 = data_fixture.create_database_application()
    data_fixture.create_database_table(database=database_tmp_2)
    data_fixture.create_database_table(database=database_tmp_3)
    data_fixture.create_database_table()

    databases = LocalBaserowIntegrationType.get_local_baserow_databases(integration)

    assert len(databases) == 2

    assert databases[0].id == database.id
    assert len(databases[0].tables) == 1
    assert databases[0].tables[0].id == table.id

    assert databases[1].id == database_2.id
    assert len(databases[1].tables) == 2
    print(databases[1].tables)
    assert databases[1].tables[0].id == table_2.id
    assert databases[1].tables[1].id == table_3.id


@pytest.mark.django_db
def test_get_local_baserow_databases_number_of_queries(
    data_fixture, django_assert_num_queries
):
    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=user)
    builder = data_fixture.create_builder_application(workspace=workspace)
    integration = data_fixture.create_local_baserow_integration(
        authorized_user=user, application=builder
    )
    database = data_fixture.create_database_application(user=user, workspace=workspace)
    table = data_fixture.create_database_table(database=database)

    with CaptureQueriesContext(connection) as queries:
        LocalBaserowIntegrationType.get_local_baserow_databases(integration)

    data_fixture.create_database_table(database=database)
    database_2 = data_fixture.create_database_application(
        user=user, workspace=workspace
    )
    data_fixture.create_database_table(database=database_2)

    with CaptureQueriesContext(connection) as queries_2:
        LocalBaserowIntegrationType.get_local_baserow_databases(integration)

    assert len(queries.captured_queries) == len(queries_2.captured_queries)


@pytest.mark.django_db
def test_get_integrations_serializer(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    workspace = data_fixture.create_workspace(user=user)
    application = data_fixture.create_builder_application(workspace=workspace)
    database = data_fixture.create_database_application(workspace=workspace)
    table = data_fixture.create_database_table(database=database)
    data_fixture.create_local_baserow_integration(application=application)

    url = reverse("api:integrations:list", kwargs={"application_id": application.id})

    with CaptureQueriesContext(connection) as queries:
        response = api_client.get(
            url,
            format="json",
            HTTP_AUTHORIZATION=f"JWT {token}",
        )

    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert len(response_json) == 1
    assert response_json[0]["context_data"] == {
        "databases": [
            {
                "id": database.id,
                "name": database.name,
                "order": database.order,
                "type": "database",
                "group": {"id": workspace.id, "name": workspace.name},
                "workspace": {"id": workspace.id, "name": workspace.name},
                "tables": [
                    {
                        "id": table.id,
                        "name": table.name,
                        "order": table.order,
                        "database_id": table.database_id,
                    }
                ],
            },
        ]
    }

    database_2 = data_fixture.create_database_application(workspace=workspace)
    data_fixture.create_database_table(database=database_2)
    data_fixture.create_database_table(database=database_2)

    with CaptureQueriesContext(connection) as queries_2:
        api_client.get(
            url,
            format="json",
            HTTP_AUTHORIZATION=f"JWT {token}",
        )

    assert len(queries.captured_queries) == len(queries_2.captured_queries)
