import pytest

from baserow.contrib.database.rows.handler import RowHandler
from baserow.contrib.database.table.handler import TableHandler
from baserow.contrib.database.views.models import SORT_ORDER_ASC, SORT_ORDER_DESC
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
        {
            "view_id": view.id,
            "table_id": view.table_id,
            "integration_id": integration.id,
        },
        user,
    )

    service = ServiceHandler().create_service(service_type, **values)

    assert service.view.id == view.id
    assert service.table.id == view.table_id


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
        table=view.table,
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
        table=table,
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
        table=table,
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
        integration=integration, table=None
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
        {
            "view_id": view.id,
            "table_id": view.table_id,
            "integration_id": integration.id,
            "row_id": "1",
        },
        user,
    )
    service = ServiceHandler().create_service(service_type, **values)

    assert service.view.id == view.id
    assert service.table.id == view.table_id
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

    service_type = LocalBaserowGetRowUserServiceType()
    values = service_type.prepare_values(
        {"table_id": None, "integration_id": None}, user
    )

    ServiceHandler().update_service(service_type, service, **values)

    service.refresh_from_db()

    assert service.specific.table is None
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
        integration=integration, view=view, table=table, row_id="get('test')"
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
        integration=integration, view=view, table=table, row_id="1"
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
    integration = data_fixture.create_local_baserow_integration(
        application=page.builder, user=user
    )

    service = data_fixture.create_local_baserow_get_row_service(
        integration=integration, table=table, row_id="1", search_query="Au"
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
        LocalBaserowGetRowUserServiceType().dispatch_data(
            service, runtime_formula_context  # type: ignore
        )


@pytest.mark.django_db
def test_local_baserow_get_row_service_dispatch_data_validation_error(data_fixture):
    user = data_fixture.create_user()
    page = data_fixture.create_builder_page(user=user)
    table = data_fixture.create_database_table(user=user)
    integration = data_fixture.create_local_baserow_integration(
        application=page.builder, user=user
    )

    service = data_fixture.create_local_baserow_get_row_service(
        integration=integration, table=None, row_id="1"
    )
    service_type = LocalBaserowGetRowUserServiceType()

    runtime_formula_context = {"test": "1"}

    with pytest.raises(ServiceImproperlyConfigured):
        service_type.dispatch_data(service, runtime_formula_context)  # type: ignore

    service = data_fixture.create_local_baserow_get_row_service(
        integration=integration, table=table, row_id="get('test')"
    )

    runtime_formula_context = {"test": ""}

    with pytest.raises(ServiceImproperlyConfigured):
        service_type.dispatch_data(service, runtime_formula_context)  # type: ignore

    service = data_fixture.create_local_baserow_get_row_service(
        integration=integration, table=table, row_id="wrong formula"
    )

    with pytest.raises(ServiceImproperlyConfigured):
        service_type.dispatch_data(service, runtime_formula_context)  # type: ignore


@pytest.mark.django_db
def test_local_baserow_get_row_service_dispatch_data_row_not_exist(data_fixture):
    user = data_fixture.create_user()
    page = data_fixture.create_builder_page(user=user)
    table = data_fixture.create_database_table(user=user)
    integration = data_fixture.create_local_baserow_integration(
        application=page.builder, user=user
    )

    service = data_fixture.create_local_baserow_get_row_service(
        integration=integration, table=table, row_id="get('test')"
    )

    runtime_formula_context = {"test": "999"}

    with pytest.raises(DoesNotExist):
        LocalBaserowGetRowUserServiceType().dispatch_data(
            service, runtime_formula_context  # type: ignore
        )


@pytest.mark.django_db
def test_local_baserow_list_rows_service_dispatch_data_with_view_and_service_filters(
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
        view=view, table=table, integration=integration
    )

    dispatch_data = service_type.dispatch_data(service)
    queryset = dispatch_data["data"]
    assert list(queryset.values_list("id", flat=True)) == [row_1.id, row_2.id]

    data_fixture.create_local_baserow_table_service_filter(
        service=service, field=field, value="Cheese"
    )

    dispatch_data = service_type.dispatch_data(service)
    queryset = dispatch_data["data"]
    assert list(queryset.values_list("id", flat=True)) == [row_1.id]


@pytest.mark.django_db
def test_local_baserow_list_rows_service_dispatch_data_with_varying_filter_types(
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
            ("Cost", "number", {}),
        ],
    )
    ingredient = table.field_set.get(name="Ingredient")
    cost = table.field_set.get(name="Cost")
    [row_1, row_2, row_3, _] = RowHandler().create_rows(
        user,
        table,
        rows_values=[
            {f"field_{ingredient.id}": "Duck", f"field_{cost.id}": 50},
            {f"field_{ingredient.id}": "Duckling", f"field_{cost.id}": 25},
            {f"field_{ingredient.id}": "Goose", f"field_{cost.id}": 150},
            {f"field_{ingredient.id}": "Beef", f"field_{cost.id}": 250},
        ],
    )

    view = data_fixture.create_grid_view(
        user, table=table, created_by=user, filter_type="OR"
    )
    service_type = LocalBaserowListRowsUserServiceType()
    service = data_fixture.create_local_baserow_list_rows_service(
        view=view, table=table, integration=integration, filter_type="OR"
    )

    # (ingredient=Duck OR ingredient=Goose) AND (cost=150).
    equals_duck = data_fixture.create_view_filter(
        view=view, field=ingredient, type="equal", value="Duck"
    )
    equals_goose = data_fixture.create_view_filter(
        view=view, field=ingredient, type="equal", value="Goose"
    )
    cost_150 = data_fixture.create_local_baserow_table_service_filter(
        service=service, field=cost, value="150"
    )
    dispatch_data = service_type.dispatch_data(service)
    assert list(dispatch_data["data"].values_list("id", flat=True)) == [
        row_3.id,  # Only Goose has a cost of 150.
    ]
    cost_150.delete()
    equals_duck.delete()
    equals_goose.delete()

    # (ingredient contains Duck) AND (cost=25 OR cost=50).
    data_fixture.create_view_filter(
        view=view, field=ingredient, type="contains", value="Duck"
    )
    data_fixture.create_local_baserow_table_service_filter(
        service=service, field=cost, value="25"
    )
    data_fixture.create_local_baserow_table_service_filter(
        service=service, field=cost, value="50"
    )
    dispatch_data = service_type.dispatch_data(service)
    assert list(dispatch_data["data"].values_list("id", flat=True)) == [
        row_1.id,  # Duck
        row_2.id,  # Duckling
    ]


@pytest.mark.django_db
def test_local_baserow_list_rows_service_dispatch_data_with_view_and_service_sorts(
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
            ("Cost", "number", {}),
        ],
    )
    ingredients = table.field_set.get(name="Ingredient")
    cost = table.field_set.get(name="Cost")
    [row_1, row_2, row_3] = RowHandler().create_rows(
        user,
        table,
        rows_values=[
            {f"field_{ingredients.id}": "Duck", f"field_{cost.id}": 50},
            {f"field_{ingredients.id}": "Goose", f"field_{cost.id}": 150},
            {f"field_{ingredients.id}": "Beef", f"field_{cost.id}": 250},
        ],
    )
    view = data_fixture.create_grid_view(user, table=table, created_by=user)
    service_type = LocalBaserowListRowsUserServiceType()
    service = data_fixture.create_local_baserow_list_rows_service(
        view=view, table=table, integration=integration
    )

    # A `ViewSort` alone.
    view_sort = data_fixture.create_view_sort(view=view, field=ingredients, order="ASC")
    dispatch_data = service_type.dispatch_data(service)
    assert list(dispatch_data["data"].values_list("id", flat=True)) == [
        row_3.id,
        row_1.id,
        row_2.id,
    ]
    view_sort.delete()

    # A `ServiceSort` alone.
    service_sort = data_fixture.create_local_baserow_table_service_sort(
        service=service, field=cost, order=SORT_ORDER_DESC
    )
    dispatch_data = service_type.dispatch_data(service)
    assert list(dispatch_data["data"].values_list("id", flat=True)) == [
        row_3.id,
        row_2.id,
        row_1.id,
    ]
    service_sort.delete()

    # A `ViewSort` & `ServiceSort`, the latter is used.
    data_fixture.create_local_baserow_table_service_sort(
        service=service, field=cost, order=SORT_ORDER_ASC
    )
    data_fixture.create_view_sort(view=view, field=cost, order=SORT_ORDER_DESC)
    dispatch_data = service_type.dispatch_data(service)
    assert list(dispatch_data["data"].values_list("id", flat=True)) == [
        row_1.id,
        row_2.id,
        row_3.id,
    ]
