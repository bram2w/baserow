import pytest

from baserow.contrib.integrations.local_baserow.models import LocalBaserowGetRow
from baserow.core.services.exceptions import (
    ServiceDoesNotExist,
    ServiceImproperlyConfigured,
)
from baserow.core.services.handler import ServiceHandler
from baserow.core.services.models import Service
from baserow.core.services.registries import service_type_registry


@pytest.mark.django_db
def test_create_service(data_fixture):
    user = data_fixture.create_user()
    integration = data_fixture.create_local_baserow_integration(user=user)

    service_type = service_type_registry.get("local_baserow_get_row")

    service = ServiceHandler().create_service(service_type, integration=integration)

    assert service.integration.id == integration.id

    assert Service.objects.count() == 1

    service = ServiceHandler().create_service(service_type)

    assert service.integration is None


@pytest.mark.django_db
def test_get_service(data_fixture):
    service = data_fixture.create_local_baserow_get_row_service()
    assert ServiceHandler().get_service(service.id).id == service.id


@pytest.mark.django_db
def test_get_service_does_not_exist(data_fixture):
    with pytest.raises(ServiceDoesNotExist):
        assert ServiceHandler().get_service(0)


@pytest.mark.django_db
def test_get_services(data_fixture):
    integration = data_fixture.create_local_baserow_integration()
    service1 = data_fixture.create_local_baserow_get_row_service(
        integration=integration
    )
    service2 = data_fixture.create_local_baserow_get_row_service(
        integration=integration
    )
    service3 = data_fixture.create_local_baserow_get_row_service(
        integration=integration
    )

    services = ServiceHandler().get_services(integration=integration)

    assert [e.id for e in services] == [
        service1.id,
        service2.id,
        service3.id,
    ]

    assert isinstance(services[0], LocalBaserowGetRow)


@pytest.mark.django_db
def test_update_service(data_fixture):
    service = data_fixture.create_local_baserow_get_row_service()
    table = data_fixture.create_database_table()

    service_type = service_type_registry.get("local_baserow_get_row")

    service_updated = ServiceHandler().update_service(
        service_type, service, table=table
    )

    assert service_updated.table.id == table.id


@pytest.mark.django_db
def test_update_service_invalid_values(data_fixture):
    service = data_fixture.create_local_baserow_get_row_service()

    service_type = service_type_registry.get("local_baserow_get_row")

    service_updated = ServiceHandler().update_service(
        service_type, service, nonsense="hello"
    )

    assert not hasattr(service_updated, "nonsense")


@pytest.mark.django_db
def test_delete_service(data_fixture):
    service = data_fixture.create_local_baserow_get_row_service()

    ServiceHandler().delete_service(service)

    assert Service.objects.count() == 0


@pytest.mark.django_db
def test_dispatch_local_baserow_get_row_service_missing_integration(data_fixture):
    service = data_fixture.create_local_baserow_get_row_service(integration=None)

    with pytest.raises(ServiceImproperlyConfigured):
        ServiceHandler().dispatch_service(service, {})
