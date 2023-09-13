from unittest.mock import Mock, patch

from django.db import transaction

import pytest

from baserow.contrib.database.rows.handler import RowHandler
from baserow.contrib.database.table.handler import TableHandler
from baserow.contrib.integrations.local_baserow.service_types import (
    LocalBaserowGetRowUserServiceType,
    LocalBaserowListRowsUserServiceType,
)
from baserow.core.exceptions import PermissionException
from baserow.core.services.exceptions import DoesNotExist, ServiceImproperlyConfigured
from baserow.core.services.handler import ServiceHandler
from baserow.core.services.registries import service_type_registry


@pytest.mark.django_db
def test_create_local_baserow_list_rows_service(data_fixture):
    user = data_fixture.create_user()
    page = data_fixture.create_builder_page(user=user)
    view = data_fixture.create_grid_view(user)
    integration = data_fixture.create_local_baserow_integration(
        application=page.builder, user=user
    )

    service_type = service_type_registry.get("local_baserow_list_rows")

    values = service_type.prepare_values(
        {"view_id": view.id, "integration_id": integration.id}, user
    )

    service = ServiceHandler().create_service(service_type, **values)

    assert service.view.id == view.id


@pytest.mark.django_db
def test_update_local_baserow_list_rows_service(data_fixture):
    user = data_fixture.create_user()
    page = data_fixture.create_builder_page(user=user)
    view = data_fixture.create_grid_view(user)
    integration = data_fixture.create_local_baserow_integration(
        application=page.builder, user=user
    )
    service = data_fixture.create_local_baserow_list_rows_service(
        integration=integration,
        view=view,
    )

    service_type = service_type_registry.get("local_baserow_list_rows")

    values = service_type.prepare_values(
        {"view_id": None, "integration_id": None}, user
    )

    ServiceHandler().update_service(service_type, service, **values)

    service.refresh_from_db()

    assert service.specific.view is None
    assert service.specific.integration is None


@pytest.mark.django_db
def test_local_baserow_list_rows_service_dispatch_transform(data_fixture):
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
    view = data_fixture.create_grid_view(user, table=table)
    integration = data_fixture.create_local_baserow_integration(
        application=page.builder, user=user
    )

    service = data_fixture.create_local_baserow_list_rows_service(
        integration=integration,
        view=view,
    )

    service_type = LocalBaserowListRowsUserServiceType()
    dispatch_data = service_type.dispatch_data(service)
    result = service_type.dispatch_transform(dispatch_data)

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
def test_local_baserow_list_rows_service_dispatch_data_permission_denied(
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
    view = data_fixture.create_grid_view(user, table=table)
    integration = data_fixture.create_local_baserow_integration(
        application=page.builder, user=user
    )

    service = data_fixture.create_local_baserow_list_rows_service(
        integration=integration,
        view=view,
    )

    with stub_check_permissions(raise_permission_denied=True), pytest.raises(
        PermissionException
    ):
        LocalBaserowListRowsUserServiceType().dispatch_data(service)


@pytest.mark.django_db
def test_local_baserow_list_rows_service_dispatch_data_validation_error(data_fixture):
    user = data_fixture.create_user()
    page = data_fixture.create_builder_page(user=user)
    integration = data_fixture.create_local_baserow_integration(
        application=page.builder, user=user
    )
    service = data_fixture.create_local_baserow_list_rows_service(
        integration=integration, view=None
    )

    with pytest.raises(ServiceImproperlyConfigured):
        LocalBaserowListRowsUserServiceType().dispatch_data(service)


@pytest.mark.django_db
def test_create_local_baserow_get_row_service(data_fixture):
    user = data_fixture.create_user()
    page = data_fixture.create_builder_page(user=user)
    view = data_fixture.create_grid_view(user)
    integration = data_fixture.create_local_baserow_integration(
        application=page.builder, user=user
    )

    service_type = LocalBaserowGetRowUserServiceType()
    values = service_type.prepare_values(
        {"view_id": view.id, "integration_id": integration.id, "row_id": "1"}, user
    )
    service = ServiceHandler().create_service(service_type, **values)

    assert service.view.id == view.id
    assert service.row_id == "1"


@pytest.mark.django_db
def test_update_local_baserow_get_row_service(data_fixture):
    user = data_fixture.create_user()
    page = data_fixture.create_builder_page(user=user)
    view = data_fixture.create_grid_view(user)
    integration = data_fixture.create_local_baserow_integration(
        application=page.builder, user=user
    )
    service = data_fixture.create_local_baserow_get_row_service(
        integration=integration,
        view=view,
    )

    service_type = LocalBaserowGetRowUserServiceType()
    values = service_type.prepare_values(
        {"view_id": None, "integration_id": None}, user
    )

    ServiceHandler().update_service(service_type, service, **values)

    service.refresh_from_db()

    assert service.specific.view is None
    assert service.specific.integration is None


@pytest.mark.django_db
def test_local_baserow_get_row_service_dispatch_transform(data_fixture):
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
    view = data_fixture.create_grid_view(user, table=table)
    integration = data_fixture.create_local_baserow_integration(
        application=page.builder, user=user
    )

    service = data_fixture.create_local_baserow_get_row_service(
        integration=integration, view=view, row_id="get('test')"
    )
    service_type = LocalBaserowGetRowUserServiceType()

    runtime_formula_context = {"test": 2}
    dispatch_data = service_type.dispatch_data(
        service, runtime_formula_context  # type: ignore
    )
    result = service_type.dispatch_transform(dispatch_data)

    assert result == {
        "id": rows[1].id,
        "Name": "Audi",
        "My Color": "Orange",
        "order": "1.00000000000000000000",
    }


@pytest.mark.django_db
def test_local_baserow_get_row_service_dispatch_data_with_view_filter(data_fixture):
    # Demonstrates that you can fetch a specific row (1) and filter for a specific
    # value to exclude it from the `dispatch_data` result.
    user = data_fixture.create_user()
    page = data_fixture.create_builder_page(user=user)
    table, fields, rows = data_fixture.build_table(
        user=user,
        columns=[
            ("Name", "text"),
        ],
        rows=[
            ["BMW"],
            ["Audi"],
        ],
    )
    view = data_fixture.create_grid_view(user, table=table)
    data_fixture.create_view_filter(
        view=view, field=fields[0], type="contains", value="Au"
    )
    integration = data_fixture.create_local_baserow_integration(
        application=page.builder, user=user
    )

    service = data_fixture.create_local_baserow_get_row_service(
        integration=integration, view=view, row_id="1"
    )

    runtime_formula_context = {}
    with pytest.raises(DoesNotExist):
        LocalBaserowGetRowUserServiceType().dispatch_data(
            service, runtime_formula_context  # type: ignore
        )


@pytest.mark.django_db
def test_local_baserow_get_row_service_dispatch_data_with_service_search(data_fixture):
    # Demonstrates that you can fetch a specific row (1) and search for a specific
    # value to exclude it from the `dispatch_data` result.
    user = data_fixture.create_user()
    page = data_fixture.create_builder_page(user=user)
    table, fields, rows = data_fixture.build_table(
        user=user,
        columns=[
            ("Name", "text"),
        ],
        rows=[
            ["BMW"],
            ["Audi"],
        ],
    )
    view = data_fixture.create_grid_view(user, table=table)
    integration = data_fixture.create_local_baserow_integration(
        application=page.builder, user=user
    )

    service = data_fixture.create_local_baserow_get_row_service(
        integration=integration, view=view, row_id="1", search_query="Au"
    )

    runtime_formula_context = {}
    with pytest.raises(DoesNotExist):
        LocalBaserowGetRowUserServiceType().dispatch_data(
            service, runtime_formula_context  # type: ignore
        )


@pytest.mark.django_db
def test_local_baserow_get_row_service_dispatch_data_permission_denied(
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
    view = data_fixture.create_grid_view(user, table=table)
    integration = data_fixture.create_local_baserow_integration(
        application=page.builder, user=user
    )

    service = data_fixture.create_local_baserow_get_row_service(
        integration=integration, view=view, row_id="get('test')"
    )

    runtime_formula_context = {"test": "1"}

    with stub_check_permissions(raise_permission_denied=True), pytest.raises(
        PermissionException
    ):
        LocalBaserowGetRowUserServiceType().dispatch_data(
            service, runtime_formula_context  # type: ignore
        )


@pytest.mark.django_db
def test_local_baserow_get_row_service_dispatch_data_validation_error(data_fixture):
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
    view = data_fixture.create_grid_view(user, table=table)
    integration = data_fixture.create_local_baserow_integration(
        application=page.builder, user=user
    )

    service = data_fixture.create_local_baserow_get_row_service(
        integration=integration, view=None, row_id="1"
    )
    service_type = LocalBaserowGetRowUserServiceType()

    runtime_formula_context = {"test": "1"}

    with pytest.raises(ServiceImproperlyConfigured):
        service_type.dispatch_data(service, runtime_formula_context)  # type: ignore

    service = data_fixture.create_local_baserow_get_row_service(
        integration=integration, view=view, row_id="get('test')"
    )

    runtime_formula_context = {"test": ""}

    with pytest.raises(ServiceImproperlyConfigured):
        service_type.dispatch_data(service, runtime_formula_context)  # type: ignore

    service = data_fixture.create_local_baserow_get_row_service(
        integration=integration, view=view, row_id="wrong formula"
    )

    with pytest.raises(ServiceImproperlyConfigured):
        service_type.dispatch_data(service, runtime_formula_context)  # type: ignore


@pytest.mark.django_db
def test_local_baserow_get_row_service_dispatch_data_row_not_exist(data_fixture):
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
    view = data_fixture.create_grid_view(user, table=table)
    integration = data_fixture.create_local_baserow_integration(
        application=page.builder, user=user
    )

    service = data_fixture.create_local_baserow_get_row_service(
        integration=integration, view=view, row_id="get('test')"
    )

    runtime_formula_context = {"test": "999"}

    with pytest.raises(DoesNotExist):
        LocalBaserowGetRowUserServiceType().dispatch_data(
            service, runtime_formula_context  # type: ignore
        )


@patch("baserow.contrib.integrations.local_baserow.mixins.ViewHandler")
def test_local_baserow_filterable_view_service_mixin_without_model(
    mock_view_handler,
):
    mock_model = Mock()
    mock_service = Mock()
    mock_service.view.table.get_model.return_value = mock_model
    service_type = LocalBaserowListRowsUserServiceType()
    service_type.get_dispatch_filters(mock_service)
    assert mock_service.view.table.get_model.called
    mock_view_handler().get_filter_builder.assert_called_with(
        mock_service.view, mock_model
    )


@pytest.mark.django_db
def test_local_baserow_list_rows_service_dispatch_data_with_view_filter(
    data_fixture,
):
    user = data_fixture.create_user()
    builder = data_fixture.create_builder_application(user=user)
    integration = data_fixture.create_local_baserow_integration(
        application=builder, user=user
    )
    database = data_fixture.create_database_application(workspace=builder.workspace)
    table = TableHandler().create_table_and_fields(
        user=user,
        database=database,
        name=data_fixture.fake.name(),
        fields=[
            ("Ingredient", "text", {}),
        ],
    )
    field = table.field_set.get(name="Ingredient")
    [row_1, row_2, _] = RowHandler().create_rows(
        user,
        table,
        rows_values=[
            {f"field_{field.id}": "Cheese"},
            {f"field_{field.id}": "Chicken"},
            {f"field_{field.id}": "Milk"},
        ],
    )
    view = data_fixture.create_grid_view(user, table=table, created_by=user)
    data_fixture.create_view_filter(view=view, field=field, type="contains", value="Ch")

    service_type = LocalBaserowListRowsUserServiceType()
    service = data_fixture.create_local_baserow_list_rows_service(
        view=view, integration=integration
    )

    dispatch_data = service_type.dispatch_data(service)
    queryset = dispatch_data["data"]
    assert list(queryset.values_list("id", flat=True)) == [row_1.id, row_2.id]


@patch("baserow.contrib.integrations.local_baserow.mixins.ViewHandler")
def test_local_baserow_sortable_view_service_mixin_without_model(
    mock_view_handler,
):
    mock_model = Mock()
    mock_service = Mock()
    handler = mock_view_handler()
    mock_service.view.table.get_model.return_value = mock_model
    handler.get_view_sorts.return_value = (None, None)
    service_type = LocalBaserowListRowsUserServiceType()
    service_type.get_dispatch_sorts(mock_service)
    assert mock_service.view.table.get_model.called
    handler.get_view_sorts.assert_called_with(mock_service.view, mock_model)


@pytest.mark.django_db
def test_local_baserow_list_rows_service_dispatch_data_with_view_sort(data_fixture):
    user = data_fixture.create_user()
    builder = data_fixture.create_builder_application(user=user)
    integration = data_fixture.create_local_baserow_integration(
        application=builder, user=user
    )
    database = data_fixture.create_database_application(workspace=builder.workspace)
    table = TableHandler().create_table_and_fields(
        user=user,
        database=database,
        name=data_fixture.fake.name(),
        fields=[
            ("Ingredient", "text", {}),
        ],
    )
    field = table.field_set.get(name="Ingredient")
    [row_1, row_2, row_3] = RowHandler().create_rows(
        user,
        table,
        rows_values=[
            {f"field_{field.id}": "Duck"},
            {f"field_{field.id}": "Goose"},
            {f"field_{field.id}": "Beef"},
        ],
    )
    view = data_fixture.create_grid_view(user, table=table, created_by=user)
    data_fixture.create_view_sort(view=view, field=field, order="ASC")

    service_type = LocalBaserowListRowsUserServiceType()
    service = data_fixture.create_local_baserow_list_rows_service(
        view=view, integration=integration
    )

    dispatch_data = service_type.dispatch_data(service)
    queryset = dispatch_data["data"]
    assert list(queryset.values_list("id", flat=True)) == [row_3.id, row_1.id, row_2.id]


@pytest.mark.django_db(transaction=True)
def test_local_baserow_list_rows_service_dispatch_data_with_service_search(
    data_fixture,
):
    with transaction.atomic():
        user = data_fixture.create_user()
        builder = data_fixture.create_builder_application(user=user)
        integration = data_fixture.create_local_baserow_integration(
            application=builder, user=user
        )
        database = data_fixture.create_database_application(workspace=builder.workspace)
        table = TableHandler().create_table_and_fields(
            user=user,
            database=database,
            name=data_fixture.fake.name(),
            fields=[
                ("Ingredient", "text", {}),
            ],
        )
        view = data_fixture.create_grid_view(user, table=table, created_by=user)
        field = table.field_set.get(name="Ingredient")
        [row_1, row_2, _] = RowHandler().create_rows(
            user,
            table,
            rows_values=[
                {f"field_{field.id}": "Cheese"},
                {f"field_{field.id}": "Chicken"},
                {f"field_{field.id}": "Beef"},
            ],
        )

    service_type = LocalBaserowListRowsUserServiceType()
    service = data_fixture.create_local_baserow_list_rows_service(
        view=view, integration=integration, search_query="ch"
    )

    dispatch_data = service_type.dispatch_data(service)
    queryset = dispatch_data["data"]
    assert list(queryset.values_list("id", flat=True)) == [row_1.id, row_2.id]
