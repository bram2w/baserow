import pytest

from baserow.contrib.builder.data_sources.service import DataSourceService
from baserow.core.services.registries import service_type_registry


@pytest.mark.django_db
def test_create_local_baserow_list_rows_data_source(data_fixture):
    user = data_fixture.create_user()
    page = data_fixture.create_builder_page(user=user)
    table = data_fixture.create_database_table(user=user)
    integration = data_fixture.create_local_baserow_integration(
        application=page.builder, user=user
    )

    service_type = service_type_registry.get("local_baserow_list_rows")

    data_source = DataSourceService().create_data_source(
        user,
        service_type=service_type,
        page=page,
        table_id=table.id,
        integration_id=integration.id,
    )

    assert data_source.service.table.id == table.id

    DataSourceService().update_data_source(
        user, data_source, service_type=service_type, table_id=None, integration_id=None
    )

    data_source.refresh_from_db()

    assert data_source.service.specific.table is None


@pytest.mark.django_db
def test_create_local_baserow_get_row_data_source(data_fixture):
    user = data_fixture.create_user()
    page = data_fixture.create_builder_page(user=user)
    table = data_fixture.create_database_table(user=user)
    integration = data_fixture.create_local_baserow_integration(
        application=page.builder, user=user
    )

    service_type = service_type_registry.get("local_baserow_get_row")

    data_source = DataSourceService().create_data_source(
        user,
        service_type=service_type,
        page=page,
        table_id=table.id,
        integration_id=integration.id,
    )

    assert data_source.service.table.id == table.id

    DataSourceService().update_data_source(
        user, data_source, service_type=service_type, table_id=None, integration_id=None
    )

    data_source.refresh_from_db()

    assert data_source.service.specific.table is None
