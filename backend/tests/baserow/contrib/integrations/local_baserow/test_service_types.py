import pytest

from baserow.core.exceptions import PermissionException
from baserow.core.services.exceptions import DoesNotExist, ServiceImproperlyConfigured
from baserow.core.services.handler import ServiceHandler
from baserow.core.services.registries import service_type_registry


@pytest.mark.django_db
def test_create_local_baserow_list_rows_service(data_fixture):
    user = data_fixture.create_user()
    page = data_fixture.create_builder_page(user=user)
    table = data_fixture.create_database_table(user=user)
    integration = data_fixture.create_local_baserow_integration(
        application=page.builder, user=user
    )

    service_type = service_type_registry.get("local_baserow_list_rows")

    values = service_type.prepare_values(
        {"table_id": table.id, "integration_id": integration.id}, user
    )

    service = ServiceHandler().create_service(service_type, **values)

    assert service.table.id == table.id


@pytest.mark.django_db
def test_update_local_baserow_list_rows_service(data_fixture):
    user = data_fixture.create_user()
    page = data_fixture.create_builder_page(user=user)
    table = data_fixture.create_database_table(user=user)
    integration = data_fixture.create_local_baserow_integration(
        application=page.builder, user=user
    )
    service = data_fixture.create_local_baserow_list_rows_service(
        integration=integration,
        table=table,
    )

    service_type = service_type_registry.get("local_baserow_list_rows")

    values = service_type.prepare_values(
        {"table_id": None, "integration_id": None}, user
    )

    ServiceHandler().update_service(service_type, service, **values)

    service.refresh_from_db()

    assert service.specific.table is None
    assert service.specific.integration is None


@pytest.mark.django_db
def test_dispatch_local_baserow_list_rows_service(data_fixture):
    user = data_fixture.create_user()
    page = data_fixture.create_builder_page(user=user)
    table, fields, rows = data_fixture.build_table(
        user=user,
        columns=[
            ("Name", "text"),
            ("My Color", "text"),
        ],
        rows=[
            ["BMW", "Blue"],
            ["Audi", "Orange"],
        ],
    )
    integration = data_fixture.create_local_baserow_integration(
        application=page.builder, user=user
    )

    service = data_fixture.create_local_baserow_list_rows_service(
        integration=integration,
        table=table,
    )

    runtime_formula_context = {}

    result = ServiceHandler().dispatch_service(service, runtime_formula_context)

    assert [dict(r) for r in result] == [
        {
            "id": rows[0].id,
            "Name": "BMW",
            "My Color": "Blue",
            "order": "1.00000000000000000000",
        },
        {
            "id": rows[1].id,
            "Name": "Audi",
            "My Color": "Orange",
            "order": "1.00000000000000000000",
        },
    ]


@pytest.mark.django_db
def test_dispatch_local_baserow_list_rows_service_permission_denied(
    data_fixture, stub_check_permissions
):
    user = data_fixture.create_user()
    page = data_fixture.create_builder_page(user=user)
    table, fields, rows = data_fixture.build_table(
        user=user,
        columns=[
            ("Name", "text"),
            ("My Color", "text"),
        ],
        rows=[
            ["BMW", "Blue"],
            ["Audi", "Orange"],
        ],
    )
    integration = data_fixture.create_local_baserow_integration(
        application=page.builder, user=user
    )

    service = data_fixture.create_local_baserow_list_rows_service(
        integration=integration,
        table=table,
    )

    runtime_formula_context = {}

    with stub_check_permissions(raise_permission_denied=True), pytest.raises(
        PermissionException
    ):
        ServiceHandler().dispatch_service(service, runtime_formula_context)


@pytest.mark.django_db
def test_dispatch_local_baserow_list_rows_service_validation_error(data_fixture):
    user = data_fixture.create_user()
    page = data_fixture.create_builder_page(user=user)
    table, fields, rows = data_fixture.build_table(
        user=user,
        columns=[
            ("Name", "text"),
            ("My Color", "text"),
        ],
        rows=[
            ["BMW", "Blue"],
            ["Audi", "Orange"],
        ],
    )
    integration = data_fixture.create_local_baserow_integration(
        application=page.builder, user=user
    )

    service = data_fixture.create_local_baserow_list_rows_service(
        integration=integration, table=None
    )

    runtime_formula_context = {}

    with pytest.raises(ServiceImproperlyConfigured):
        ServiceHandler().dispatch_service(service, runtime_formula_context)


@pytest.mark.django_db
def test_create_local_baserow_get_row_service(data_fixture):
    user = data_fixture.create_user()
    page = data_fixture.create_builder_page(user=user)
    table = data_fixture.create_database_table(user=user)
    integration = data_fixture.create_local_baserow_integration(
        application=page.builder, user=user
    )

    service_type = service_type_registry.get("local_baserow_get_row")

    values = service_type.prepare_values(
        {"table_id": table.id, "integration_id": integration.id, "row_id": "1"}, user
    )

    service = ServiceHandler().create_service(service_type, **values)

    assert service.table.id == table.id
    assert service.row_id == "1"


@pytest.mark.django_db
def test_update_local_baserow_get_row_service(data_fixture):
    user = data_fixture.create_user()
    page = data_fixture.create_builder_page(user=user)
    table = data_fixture.create_database_table(user=user)
    integration = data_fixture.create_local_baserow_integration(
        application=page.builder, user=user
    )
    service = data_fixture.create_local_baserow_get_row_service(
        integration=integration,
        table=table,
    )

    service_type = service.get_type()

    values = service_type.prepare_values(
        {"table_id": None, "integration_id": None}, user
    )

    ServiceHandler().update_service(service_type, service, **values)

    service.refresh_from_db()

    assert service.specific.table is None
    assert service.specific.integration is None


@pytest.mark.django_db
def test_dispatch_local_baserow_get_row_service(data_fixture):
    user = data_fixture.create_user()
    page = data_fixture.create_builder_page(user=user)
    table, fields, rows = data_fixture.build_table(
        user=user,
        columns=[
            ("Name", "text"),
            ("My Color", "text"),
        ],
        rows=[
            ["BMW", "Blue"],
            ["Audi", "Orange"],
        ],
    )
    integration = data_fixture.create_local_baserow_integration(
        application=page.builder, user=user
    )

    service = data_fixture.create_local_baserow_get_row_service(
        integration=integration, table=table, row_id="get('test')"
    )

    runtime_formula_context = {"test": 2}

    result = ServiceHandler().dispatch_service(service, runtime_formula_context)

    assert result == {
        "id": rows[1].id,
        "Name": "Audi",
        "My Color": "Orange",
        "order": "1.00000000000000000000",
    }


@pytest.mark.django_db
def test_dispatch_local_baserow_get_row_service_permission_denied(
    data_fixture, stub_check_permissions
):
    user = data_fixture.create_user()
    page = data_fixture.create_builder_page(user=user)
    table, fields, rows = data_fixture.build_table(
        user=user,
        columns=[
            ("Name", "text"),
            ("My Color", "text"),
        ],
        rows=[
            ["BMW", "Blue"],
            ["Audi", "Orange"],
        ],
    )
    integration = data_fixture.create_local_baserow_integration(
        application=page.builder, user=user
    )

    service = data_fixture.create_local_baserow_get_row_service(
        integration=integration, table=table, row_id="get('test')"
    )

    runtime_formula_context = {"test": "1"}

    with stub_check_permissions(raise_permission_denied=True), pytest.raises(
        PermissionException
    ):
        ServiceHandler().dispatch_service(service, runtime_formula_context)


@pytest.mark.django_db
def test_dispatch_local_baserow_get_row_service_validation_error(data_fixture):
    user = data_fixture.create_user()
    page = data_fixture.create_builder_page(user=user)
    table, fields, rows = data_fixture.build_table(
        user=user,
        columns=[
            ("Name", "text"),
            ("My Color", "text"),
        ],
        rows=[
            ["BMW", "Blue"],
            ["Audi", "Orange"],
        ],
    )
    integration = data_fixture.create_local_baserow_integration(
        application=page.builder, user=user
    )

    service = data_fixture.create_local_baserow_get_row_service(
        integration=integration, table=None, row_id="1"
    )

    runtime_formula_context = {"test": "1"}

    with pytest.raises(ServiceImproperlyConfigured):
        ServiceHandler().dispatch_service(service, runtime_formula_context)

    service = data_fixture.create_local_baserow_get_row_service(
        integration=integration, table=table, row_id="get('test')"
    )

    runtime_formula_context = {"test": ""}

    with pytest.raises(ServiceImproperlyConfigured):
        ServiceHandler().dispatch_service(service, runtime_formula_context)

    service = data_fixture.create_local_baserow_get_row_service(
        integration=integration, table=table, row_id="wrong formula"
    )

    with pytest.raises(ServiceImproperlyConfigured):
        ServiceHandler().dispatch_service(service, runtime_formula_context)


@pytest.mark.django_db
def test_dispatch_local_baserow_get_row_service_row_not_exist(data_fixture):
    user = data_fixture.create_user()
    page = data_fixture.create_builder_page(user=user)
    table, fields, rows = data_fixture.build_table(
        user=user,
        columns=[
            ("Name", "text"),
            ("My Color", "text"),
        ],
        rows=[
            ["BMW", "Blue"],
            ["Audi", "Orange"],
        ],
    )
    integration = data_fixture.create_local_baserow_integration(
        application=page.builder, user=user
    )

    service = data_fixture.create_local_baserow_get_row_service(
        integration=integration, table=table, row_id="get('test')"
    )

    runtime_formula_context = {"test": "999"}

    with pytest.raises(DoesNotExist):
        ServiceHandler().dispatch_service(service, runtime_formula_context)
