from unittest.mock import Mock

import pytest
from rest_framework.fields import (
    BooleanField,
    CharField,
    ChoiceField,
    DecimalField,
    FloatField,
    IntegerField,
    UUIDField,
)
from rest_framework.serializers import ListSerializer, Serializer

from baserow.contrib.database.rows.handler import RowHandler
from baserow.contrib.database.table.handler import TableHandler
from baserow.contrib.database.views.models import SORT_ORDER_ASC, SORT_ORDER_DESC
from baserow.contrib.integrations.local_baserow.service_types import (
    LocalBaserowGetRowUserServiceType,
    LocalBaserowListRowsUserServiceType,
    LocalBaserowServiceType,
)
from baserow.core.exceptions import PermissionException
from baserow.core.services.exceptions import DoesNotExist, ServiceImproperlyConfigured
from baserow.core.services.handler import ServiceHandler
from baserow.core.services.registries import service_type_registry
from baserow.test_utils.helpers import setup_interesting_test_table


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
            fields[0].db_column: "BMW",
            fields[1].db_column: "Blue",
            "order": "1.00000000000000000000",
        },
        {
            "id": rows[1].id,
            fields[0].db_column: "Audi",
            fields[1].db_column: "Orange",
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
        fields[0].db_column: "Audi",
        fields[1].db_column: "Orange",
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


@pytest.mark.django_db
def test_local_baserow_table_service_generate_schema_with_no_table(data_fixture):
    user = data_fixture.create_user()
    builder = data_fixture.create_builder_application(user=user)
    integration = data_fixture.create_local_baserow_integration(
        application=builder, user=user
    )

    get_row_service_type = LocalBaserowGetRowUserServiceType()
    get_row_service = data_fixture.create_local_baserow_get_row_service(
        integration=integration
    )
    assert get_row_service_type.generate_schema(get_row_service) is None

    list_rows_service_type = LocalBaserowListRowsUserServiceType()
    list_rows_service = data_fixture.create_local_baserow_list_rows_service(
        integration=integration
    )
    assert list_rows_service_type.generate_schema(list_rows_service) is None


@pytest.mark.django_db
def test_local_baserow_table_service_generate_schema_with_interesting_test_table(
    data_fixture,
):
    def reset_metadata(schema, field_name):
        # Responsible for resetting a schema's `metadata`,
        # it's simply a nested serialized field. Clearing it makes
        # testing this much simpler.
        for field_id, obj in schema[field_name].items():
            obj["metadata"] = {}

    user = data_fixture.create_user()
    builder = data_fixture.create_builder_application(user=user)
    integration = data_fixture.create_local_baserow_integration(
        application=builder, user=user
    )
    table, _, _, _, context = setup_interesting_test_table(
        data_fixture,
        user,
    )
    field_db_column_by_name = {
        field.name: field.db_column for field in table.field_set.all()
    }
    expected_local_baserow_table_service_schema_fields = {
        field_db_column_by_name["text"]: {
            "title": "text",
            "default": "",
            "original_type": "text",
            "metadata": {},
            "type": "string",
        },
        field_db_column_by_name["long_text"]: {
            "title": "long_text",
            "default": None,
            "original_type": "long_text",
            "metadata": {},
            "type": "string",
        },
        field_db_column_by_name["url"]: {
            "title": "url",
            "default": None,
            "original_type": "url",
            "metadata": {},
            "type": "string",
        },
        field_db_column_by_name["email"]: {
            "title": "email",
            "default": None,
            "original_type": "email",
            "metadata": {},
            "type": "string",
        },
        field_db_column_by_name["negative_int"]: {
            "title": "negative_int",
            "default": None,
            "original_type": "number",
            "metadata": {},
            "type": "string",
        },
        field_db_column_by_name["positive_int"]: {
            "title": "positive_int",
            "default": None,
            "original_type": "number",
            "metadata": {},
            "type": "string",
        },
        field_db_column_by_name["negative_decimal"]: {
            "title": "negative_decimal",
            "default": None,
            "original_type": "number",
            "metadata": {},
            "type": "string",
        },
        field_db_column_by_name["positive_decimal"]: {
            "title": "positive_decimal",
            "default": None,
            "original_type": "number",
            "metadata": {},
            "type": "string",
        },
        field_db_column_by_name["rating"]: {
            "title": "rating",
            "default": None,
            "original_type": "rating",
            "metadata": {},
            "type": "number",
        },
        field_db_column_by_name["boolean"]: {
            "title": "boolean",
            "default": None,
            "original_type": "boolean",
            "metadata": {},
            "type": "boolean",
        },
        field_db_column_by_name["datetime_us"]: {
            "title": "datetime_us",
            "default": None,
            "original_type": "date",
            "metadata": {},
            "type": "string",
        },
        field_db_column_by_name["date_us"]: {
            "title": "date_us",
            "default": None,
            "original_type": "date",
            "metadata": {},
            "type": "string",
        },
        field_db_column_by_name["datetime_eu"]: {
            "title": "datetime_eu",
            "default": None,
            "original_type": "date",
            "metadata": {},
            "type": "string",
        },
        field_db_column_by_name["date_eu"]: {
            "title": "date_eu",
            "default": None,
            "original_type": "date",
            "metadata": {},
            "type": "string",
        },
        field_db_column_by_name["datetime_eu_tzone_visible"]: {
            "title": "datetime_eu_tzone_visible",
            "default": None,
            "original_type": "date",
            "metadata": {},
            "type": "string",
        },
        field_db_column_by_name["datetime_eu_tzone_hidden"]: {
            "title": "datetime_eu_tzone_hidden",
            "default": None,
            "original_type": "date",
            "metadata": {},
            "type": "string",
        },
        field_db_column_by_name["last_modified_datetime_us"]: {
            "title": "last_modified_datetime_us",
            "default": None,
            "original_type": "last_modified",
            "metadata": {},
            "type": "string",
        },
        field_db_column_by_name["last_modified_date_us"]: {
            "title": "last_modified_date_us",
            "default": None,
            "original_type": "last_modified",
            "metadata": {},
            "type": "string",
        },
        field_db_column_by_name["last_modified_datetime_eu"]: {
            "title": "last_modified_datetime_eu",
            "default": None,
            "original_type": "last_modified",
            "metadata": {},
            "type": "string",
        },
        field_db_column_by_name["last_modified_date_eu"]: {
            "title": "last_modified_date_eu",
            "default": None,
            "original_type": "last_modified",
            "metadata": {},
            "type": "string",
        },
        field_db_column_by_name["last_modified_datetime_eu_tzone"]: {
            "title": "last_modified_datetime_eu_tzone",
            "default": None,
            "original_type": "last_modified",
            "metadata": {},
            "type": "string",
        },
        field_db_column_by_name["created_on_datetime_us"]: {
            "title": "created_on_datetime_us",
            "default": None,
            "original_type": "created_on",
            "metadata": {},
            "type": "string",
        },
        field_db_column_by_name["created_on_date_us"]: {
            "title": "created_on_date_us",
            "default": None,
            "original_type": "created_on",
            "metadata": {},
            "type": "string",
        },
        field_db_column_by_name["created_on_datetime_eu"]: {
            "title": "created_on_datetime_eu",
            "default": None,
            "original_type": "created_on",
            "metadata": {},
            "type": "string",
        },
        field_db_column_by_name["created_on_date_eu"]: {
            "title": "created_on_date_eu",
            "default": None,
            "original_type": "created_on",
            "metadata": {},
            "type": "string",
        },
        field_db_column_by_name["created_on_datetime_eu_tzone"]: {
            "title": "created_on_datetime_eu_tzone",
            "default": None,
            "original_type": "created_on",
            "metadata": {},
            "type": "string",
        },
        field_db_column_by_name["link_row"]: {
            "title": "link_row",
            "default": None,
            "original_type": "link_row",
            "metadata": {},
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"id": {"title": "id", "type": "number"}},
            },
        },
        field_db_column_by_name["self_link_row"]: {
            "title": "self_link_row",
            "default": None,
            "original_type": "link_row",
            "metadata": {},
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"id": {"title": "id", "type": "number"}},
            },
        },
        field_db_column_by_name["link_row_without_related"]: {
            "title": "link_row_without_related",
            "default": None,
            "original_type": "link_row",
            "metadata": {},
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"id": {"title": "id", "type": "number"}},
            },
        },
        field_db_column_by_name["decimal_link_row"]: {
            "title": "decimal_link_row",
            "default": None,
            "original_type": "link_row",
            "metadata": {},
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"id": {"title": "id", "type": "number"}},
            },
        },
        field_db_column_by_name["file_link_row"]: {
            "title": "file_link_row",
            "default": None,
            "original_type": "link_row",
            "metadata": {},
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"id": {"title": "id", "type": "number"}},
            },
        },
        field_db_column_by_name["file"]: {
            "title": "file",
            "default": None,
            "original_type": "file",
            "metadata": {},
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "url": {"title": "url", "type": None},
                    "thumbnails": {"title": "thumbnails", "type": None},
                    "visible_name": {"title": "visible_name", "type": "string"},
                    "name": {"title": "name", "type": "string"},
                    "size": {"title": "size", "type": "number"},
                    "mime_type": {"title": "mime_type", "type": "string"},
                    "is_image": {"title": "is_image", "type": "boolean"},
                    "image_width": {"title": "image_width", "type": "number"},
                    "image_height": {"title": "image_height", "type": "number"},
                    "uploaded_at": {"title": "uploaded_at", "type": "string"},
                },
            },
        },
        field_db_column_by_name["single_select"]: {
            "title": "single_select",
            "default": None,
            "original_type": "single_select",
            "metadata": {},
            "type": "object",
            "properties": {
                "id": {"title": "id", "type": "number"},
                "value": {"title": "value", "type": "string"},
                "color": {"title": "color", "type": "string"},
            },
        },
        field_db_column_by_name["multiple_select"]: {
            "title": "multiple_select",
            "default": None,
            "original_type": "multiple_select",
            "metadata": {},
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"title": "id", "type": "number"},
                    "value": {"title": "value", "type": "string"},
                    "color": {"title": "color", "type": "string"},
                },
            },
        },
        field_db_column_by_name["multiple_collaborators"]: {
            "title": "multiple_collaborators",
            "default": None,
            "original_type": "multiple_collaborators",
            "metadata": {},
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"title": "id", "type": "number"},
                    "name": {"title": "name", "type": "string"},
                },
            },
        },
        field_db_column_by_name["phone_number"]: {
            "title": "phone_number",
            "default": None,
            "original_type": "phone_number",
            "metadata": {},
            "type": "string",
        },
        field_db_column_by_name["formula_text"]: {
            "title": "formula_text",
            "default": None,
            "original_type": "formula",
            "metadata": {},
            "type": "string",
        },
        field_db_column_by_name["formula_int"]: {
            "title": "formula_int",
            "default": None,
            "original_type": "formula",
            "metadata": {},
            "type": "string",
        },
        field_db_column_by_name["formula_bool"]: {
            "title": "formula_bool",
            "default": None,
            "original_type": "formula",
            "metadata": {},
            "type": "boolean",
        },
        field_db_column_by_name["formula_decimal"]: {
            "title": "formula_decimal",
            "default": None,
            "original_type": "formula",
            "metadata": {},
            "type": "string",
        },
        field_db_column_by_name["formula_dateinterval"]: {
            "title": "formula_dateinterval",
            "default": None,
            "original_type": "formula",
            "metadata": {},
            "type": "string",
        },
        field_db_column_by_name["formula_date"]: {
            "title": "formula_date",
            "default": None,
            "original_type": "formula",
            "metadata": {},
            "type": "string",
        },
        field_db_column_by_name["formula_singleselect"]: {
            "title": "formula_singleselect",
            "default": None,
            "original_type": "formula",
            "metadata": {},
            "type": "object",
            "properties": {
                "id": {"title": "id", "type": "number"},
                "value": {"title": "value", "type": "string"},
                "color": {"title": "color", "type": "string"},
            },
        },
        field_db_column_by_name["formula_email"]: {
            "title": "formula_email",
            "default": None,
            "original_type": "formula",
            "metadata": {},
            "type": "string",
        },
        field_db_column_by_name["formula_link_with_label"]: {
            "title": "formula_link_with_label",
            "default": None,
            "original_type": "formula",
            "metadata": {},
            "type": "object",
            "properties": {
                "url": {"title": "url", "type": "string"},
                "label": {"title": "label", "type": "string"},
            },
        },
        field_db_column_by_name["formula_link_url_only"]: {
            "title": "formula_link_url_only",
            "default": None,
            "original_type": "formula",
            "metadata": {},
            "type": "object",
            "properties": {
                "url": {"title": "url", "type": "string"},
                "label": {"title": "label", "type": "string"},
            },
        },
        field_db_column_by_name["count"]: {
            "title": "count",
            "default": None,
            "original_type": "count",
            "metadata": {},
            "type": "string",
        },
        field_db_column_by_name["rollup"]: {
            "title": "rollup",
            "default": None,
            "original_type": "rollup",
            "metadata": {},
            "type": "string",
        },
        field_db_column_by_name["lookup"]: {
            "title": "lookup",
            "default": None,
            "original_type": "lookup",
            "metadata": {},
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"title": "id", "type": "number"},
                    "ids": {"title": "ids", "type": None},
                },
            },
        },
        "id": {"metadata": {}, "type": "number", "title": "ID"},
    }

    get_row_service_type = LocalBaserowGetRowUserServiceType()
    get_row_service = data_fixture.create_local_baserow_get_row_service(
        integration=integration, table=table
    )
    get_row_schema = get_row_service_type.generate_schema((get_row_service))
    reset_metadata(get_row_schema, "properties")

    assert get_row_schema["type"] == "object"
    assert (
        get_row_schema["properties"]
        == expected_local_baserow_table_service_schema_fields
    )

    list_rows_service_type = LocalBaserowListRowsUserServiceType()
    list_rows_service = data_fixture.create_local_baserow_list_rows_service(
        integration=integration, table=table
    )
    list_rows_schema = list_rows_service_type.generate_schema(list_rows_service)
    reset_metadata(list_rows_schema["items"], "properties")

    assert list_rows_schema["type"] == "array"
    assert (
        list_rows_schema["items"]["properties"]
        == expected_local_baserow_table_service_schema_fields
    )


def test_guess_type_for_response_serialize_field_permutations():
    TYPE_NULL = {"type": None}
    TYPE_OBJECT = {"type": "object", "properties": {}}
    TYPE_STRING = {"type": "string"}
    TYPE_NUMBER = {"type": "number"}
    TYPE_BOOLEAN = {"type": "boolean"}
    TYPE_ARRAY_CHILD_OBJECT = {
        "type": "array",
        "items": TYPE_OBJECT,
    }
    cls = LocalBaserowServiceType
    cls.model_class = Mock()
    assert (
        cls().guess_json_type_from_response_serialize_field(UUIDField()) == TYPE_STRING
    )
    assert (
        cls().guess_json_type_from_response_serialize_field(CharField()) == TYPE_STRING
    )
    assert (
        cls().guess_json_type_from_response_serialize_field(
            DecimalField(decimal_places=2, max_digits=4)
        )
        == TYPE_STRING
    )
    assert (
        cls().guess_json_type_from_response_serialize_field(FloatField()) == TYPE_STRING
    )
    assert (
        cls().guess_json_type_from_response_serialize_field(
            ChoiceField(choices=("a", "b"))
        )
        == TYPE_STRING
    )
    assert (
        cls().guess_json_type_from_response_serialize_field(IntegerField())
        == TYPE_NUMBER
    )
    assert (
        cls().guess_json_type_from_response_serialize_field(BooleanField())
        == TYPE_BOOLEAN
    )
    assert (
        cls().guess_json_type_from_response_serialize_field(
            ListSerializer(child=Serializer())
        )
        == TYPE_ARRAY_CHILD_OBJECT
    )
    assert (
        cls().guess_json_type_from_response_serialize_field(Serializer()) == TYPE_OBJECT
    )
    assert (
        cls().guess_json_type_from_response_serialize_field("unknown")  # type: ignore
        == TYPE_NULL
    )


def test_local_baserow_service_type_get_schema_for_return_type():
    mock_service = Mock(id=123)
    cls = LocalBaserowServiceType
    cls.model_class = Mock()
    properties = {"1": {"field": "value"}}

    cls.returns_list = True
    assert cls().get_schema_for_return_type(mock_service, properties) == {
        "type": "array",
        "items": {"properties": properties, "type": "object"},
        "title": "Service123Schema",
    }

    cls.returns_list = False
    assert cls().get_schema_for_return_type(mock_service, properties) == {
        "type": "object",
        "properties": properties,
        "title": "Service123Schema",
    }


def test_local_baserow_table_service_type_schema_name():
    mock_service = Mock(table_id=123)
    assert (
        LocalBaserowGetRowUserServiceType().get_schema_name(mock_service)
        == "Table123Schema"
    )
    assert (
        LocalBaserowListRowsUserServiceType().get_schema_name(mock_service)
        == "Table123Schema"
    )
