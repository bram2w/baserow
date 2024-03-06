from collections import defaultdict
from io import BytesIO
from typing import Any
from unittest.mock import Mock

import pytest
from rest_framework.exceptions import ValidationError
from rest_framework.exceptions import ValidationError as DRFValidationError
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

from baserow.contrib.builder.data_sources.builder_dispatch_context import (
    BuilderDispatchContext,
)
from baserow.contrib.builder.data_sources.service import DataSourceService
from baserow.contrib.builder.workflow_actions.models import EventTypes
from baserow.contrib.database.fields.handler import FieldHandler
from baserow.contrib.database.rows.handler import RowHandler
from baserow.contrib.database.table.handler import TableHandler
from baserow.contrib.database.views.models import SORT_ORDER_ASC, SORT_ORDER_DESC
from baserow.contrib.integrations.local_baserow.models import (
    LocalBaserowGetRow,
    LocalBaserowListRows,
    LocalBaserowUpsertRow,
)
from baserow.contrib.integrations.local_baserow.service_types import (
    LocalBaserowGetRowUserServiceType,
    LocalBaserowListRowsUserServiceType,
    LocalBaserowServiceType,
    LocalBaserowTableServiceType,
    LocalBaserowUpsertRowServiceType,
)
from baserow.core.exceptions import PermissionException
from baserow.core.handler import CoreHandler
from baserow.core.registries import ImportExportConfig
from baserow.core.services.dispatch_context import DispatchContext
from baserow.core.services.exceptions import DoesNotExist, ServiceImproperlyConfigured
from baserow.core.services.handler import ServiceHandler
from baserow.core.services.registries import service_type_registry
from baserow.core.utils import MirrorDict
from baserow.test_utils.helpers import setup_interesting_test_table


def fake_import_formula(formula, id_mapping):
    return formula


class FakeDispatchContext(DispatchContext):
    def range(self, service):
        return [0, 100]

    def __getitem__(self, key: str) -> Any:
        if key == "test":
            return 2
        if key == "test1":
            return 1
        if key == "test2":
            return ""
        if key == "test999":
            return "999"

        return super().__getitem__(key)


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
def test_export_import_local_baserow_list_rows_service(data_fixture):
    user = data_fixture.create_user()
    path_params = [
        {"name": "id", "type": "numeric"},
        {"name": "filter", "type": "text"},
    ]
    page = data_fixture.create_builder_page(
        path="/page/:id/:filter/", path_params=path_params
    )
    table, fields, rows = data_fixture.build_table(
        user=user,
        columns=[
            ("Name", "text"),
        ],
        rows=[
            ["BMW"],
        ],
    )
    view = data_fixture.create_grid_view(user, table=table)
    service_type = service_type_registry.get("local_baserow_list_rows")
    integration = data_fixture.create_local_baserow_integration(
        application=page.builder, user=user
    )
    service = data_fixture.create_local_baserow_list_rows_service(
        integration=integration,
        view=view,
        table=view.table,
        search_query="get('page_parameter.id')",
    )

    field = fields[0]
    service_filter = data_fixture.create_local_baserow_table_service_filter(
        service=service, field=field, value="get('page_parameter.filter')", order=0
    )
    service_sort = data_fixture.create_local_baserow_table_service_sort(
        service=service, field=field, order_by=SORT_ORDER_ASC, order=0
    )

    exported = service_type.export_serialized(service)

    assert exported == {
        "id": service.id,
        "type": service_type.type,
        "view_id": service.view_id,
        "table_id": service.table_id,
        "integration_id": service.integration_id,
        "search_query": service.search_query,
        "filters": [
            {
                "field_id": service_filter.field_id,
                "type": service_filter.type,
                "value": service_filter.value,
                "value_is_formula": service_filter.value_is_formula,
            }
        ],
        "sortings": [
            {
                "field_id": service_sort.field_id,
                "order_by": service_sort.order_by,
            }
        ],
    }

    id_mapping = {}

    service: LocalBaserowListRows = service_type.import_serialized(  # type: ignore
        integration, exported, id_mapping, import_formula=fake_import_formula
    )

    assert service.id != exported["id"]
    assert service.view_id == exported["view_id"]
    assert service.table_id == exported["table_id"]
    assert service.search_query == exported["search_query"]
    assert service.integration_id == exported["integration_id"]
    assert isinstance(service, service_type.model_class)

    assert service.service_filters.count() == 1
    service_filter = service.service_filters.get()
    assert service_filter.type == exported["filters"][0]["type"]
    assert service_filter.value == exported["filters"][0]["value"]
    assert service_filter.field_id == exported["filters"][0]["field_id"]
    assert service_filter.value_is_formula == exported["filters"][0]["value_is_formula"]

    assert service.service_sorts.count() == 1
    service_sort = service.service_sorts.get()
    assert service_sort.field_id == exported["sortings"][0]["field_id"]
    assert service_sort.order_by == exported["sortings"][0]["order_by"]

    view_2 = data_fixture.create_grid_view(user, table=table)
    field_2 = data_fixture.create_text_field(order=1, table=table)
    table_2, _, _ = data_fixture.build_table(
        columns=[("Number", "number")], rows=[[1]], user=user
    )

    id_mapping = defaultdict(lambda: MirrorDict())
    id_mapping["database_views"] = {view.id: view_2.id}  # type: ignore
    id_mapping["database_fields"] = {field.id: field_2.id}  # type: ignore
    id_mapping["database_tables"] = {table.id: table_2.id}  # type: ignore
    service: LocalBaserowListRows = service_type.import_serialized(  # type: ignore
        integration, exported, id_mapping, import_formula=fake_import_formula
    )

    assert service.view_id == view_2.id
    assert service.table_id == table_2.id

    service_filter = service.service_filters.get()
    assert service_filter.field_id == field_2.id

    service_sort = service.service_sorts.get()
    assert service_sort.field_id == field_2.id


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

    dispatch_context = FakeDispatchContext()
    dispatch_values = service_type.resolve_service_formulas(service, dispatch_context)
    dispatch_data = service_type.dispatch_data(
        service, dispatch_values, dispatch_context
    )
    result = service_type.dispatch_transform(dispatch_data)

    assert [dict(r) for r in result["results"]] == [
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
    assert result["has_next_page"] is False


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
        LocalBaserowListRowsUserServiceType().dispatch_data(
            service, {"table": table}, FakeDispatchContext()
        )


@pytest.mark.django_db
def test_local_baserow_list_rows_service_before_dispatch_validation_error(data_fixture):
    user = data_fixture.create_user()
    page = data_fixture.create_builder_page(user=user)
    integration = data_fixture.create_local_baserow_integration(
        application=page.builder, user=user
    )
    service = data_fixture.create_local_baserow_list_rows_service(
        integration=integration, table=None
    )

    with pytest.raises(ServiceImproperlyConfigured):
        LocalBaserowListRowsUserServiceType().resolve_service_formulas(
            service, FakeDispatchContext()
        )


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
def test_export_import_local_baserow_get_row_service(data_fixture):
    user = data_fixture.create_user()
    path_params = [
        {"name": "id", "type": "numeric"},
        {"name": "filter", "type": "text"},
    ]
    page = data_fixture.create_builder_page(
        path="/page/:id/:filter/", path_params=path_params
    )
    table, fields, rows = data_fixture.build_table(
        user=user,
        columns=[
            ("Name", "text"),
        ],
        rows=[
            ["BMW"],
        ],
    )
    field = fields[0]
    view = data_fixture.create_grid_view(user, table=table)
    service_type = service_type_registry.get("local_baserow_get_row")
    integration = data_fixture.create_local_baserow_integration(
        application=page.builder, user=user
    )
    service = data_fixture.create_local_baserow_get_row_service(
        integration=integration,
        row_id="1",
        view=view,
        table=view.table,
        search_query="get('page_parameter.id')",
    )
    service_filter = data_fixture.create_local_baserow_table_service_filter(
        service=service, field=field, value="get('page_parameter.filter')", order=0
    )

    exported = service_type.export_serialized(service)

    assert exported == {
        "id": service.id,
        "row_id": service.row_id,
        "type": service_type.type,
        "view_id": service.view_id,
        "table_id": service.table_id,
        "integration_id": service.integration_id,
        "search_query": service.search_query,
        "filters": [
            {
                "field_id": service_filter.field_id,
                "type": service_filter.type,
                "value": service_filter.value,
                "value_is_formula": service_filter.value_is_formula,
            }
        ],
    }

    id_mapping = {}

    service: LocalBaserowGetRow = service_type.import_serialized(  # type: ignore
        integration, exported, id_mapping, import_formula=fake_import_formula
    )

    assert service.id != exported["id"]
    assert service.row_id == exported["row_id"]
    assert service.view_id == exported["view_id"]
    assert service.table_id == exported["table_id"]
    assert service.search_query == exported["search_query"]
    assert service.integration_id == exported["integration_id"]
    assert isinstance(service, service_type.model_class)

    assert service.service_filters.count() == 1
    service_filter = service.service_filters.get()
    assert service_filter.type == exported["filters"][0]["type"]
    assert service_filter.value == exported["filters"][0]["value"]
    assert service_filter.field_id == exported["filters"][0]["field_id"]
    assert service_filter.value_is_formula == exported["filters"][0]["value_is_formula"]

    view_2 = data_fixture.create_grid_view(user, table=table)
    field_2 = data_fixture.create_text_field(order=1, table=table)
    table_2, _, _ = data_fixture.build_table(
        columns=[("Number", "number")], rows=[[1]], user=user
    )

    id_mapping = defaultdict(lambda: MirrorDict())
    id_mapping["database_views"] = {view.id: view_2.id}  # type: ignore
    id_mapping["database_fields"] = {field.id: field_2.id}  # type: ignore
    id_mapping["database_tables"] = {table.id: table_2.id}  # type: ignore
    service: LocalBaserowGetRow = service_type.import_serialized(  # type: ignore
        integration, exported, id_mapping, import_formula=fake_import_formula
    )

    assert service.view_id == view_2.id
    assert service.table_id == table_2.id

    service_filter = service.service_filters.get()
    assert service_filter.field_id == field_2.id


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

    dispatch_context = FakeDispatchContext()
    dispatch_values = LocalBaserowUpsertRowServiceType().resolve_service_formulas(
        service, dispatch_context
    )
    dispatch_data = service_type.dispatch_data(
        service, dispatch_values, dispatch_context
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
    service_type = service.get_type()

    dispatch_context = FakeDispatchContext()
    dispatch_values = service_type.resolve_service_formulas(service, dispatch_context)
    with pytest.raises(DoesNotExist):
        service_type.dispatch_data(service, dispatch_values, dispatch_context)


@pytest.mark.django_db
def test_local_baserow_get_row_service_dispatch_data_with_service_search(
    data_fixture, disable_full_text_search
):
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
        integration=integration, table=table, row_id="1", search_query="'Au'"
    )
    service_type = service.get_type()

    dispatch_context = FakeDispatchContext()
    dispatch_values = service_type.resolve_service_formulas(service, dispatch_context)
    with pytest.raises(DoesNotExist):
        service_type.dispatch_data(service, dispatch_values, dispatch_context)


@pytest.mark.django_db  # (transaction=True)
def test_local_baserow_get_row_service_dispatch_data_with_service_integer_search(
    data_fixture, disable_full_text_search
):
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
            ["42"],
        ],
    )
    integration = data_fixture.create_local_baserow_integration(
        application=page.builder, user=user
    )

    service = data_fixture.create_local_baserow_get_row_service(
        integration=integration, table=table, row_id="", search_query="42"
    )
    service_type = service.get_type()

    dispatch_context = FakeDispatchContext()
    dispatch_values = service_type.resolve_service_formulas(service, dispatch_context)

    dispatch_data = service_type.dispatch_data(
        service, dispatch_values, dispatch_context
    )
    result = service_type.dispatch_transform(dispatch_data)

    assert result == {
        "id": rows[2].id,
        fields[0].db_column: "42",
        "order": "1.00000000000000000000",
    }


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

    with stub_check_permissions(raise_permission_denied=True), pytest.raises(
        PermissionException
    ):
        LocalBaserowGetRowUserServiceType().dispatch_data(
            service, {"table": table}, FakeDispatchContext()
        )


@pytest.mark.django_db
def test_local_baserow_get_row_service_dispatch_validation_error(data_fixture):
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

    with pytest.raises(ServiceImproperlyConfigured):
        service_type.dispatch(service, FakeDispatchContext())

    service = data_fixture.create_local_baserow_get_row_service(
        integration=integration, table=table, row_id="get('test2')"
    )

    with pytest.raises(ServiceImproperlyConfigured):
        service_type.dispatch(service, FakeDispatchContext())

    service = data_fixture.create_local_baserow_get_row_service(
        integration=integration, table=table, row_id="wrong formula"
    )

    with pytest.raises(ServiceImproperlyConfigured):
        service_type.dispatch(service, FakeDispatchContext())


@pytest.mark.django_db
def test_local_baserow_get_row_service_dispatch_data_row_not_exist(data_fixture):
    user = data_fixture.create_user()
    page = data_fixture.create_builder_page(user=user)
    table = data_fixture.create_database_table(user=user)
    integration = data_fixture.create_local_baserow_integration(
        application=page.builder, user=user
    )

    service = data_fixture.create_local_baserow_get_row_service(
        integration=integration, table=table, row_id="get('test999')"
    )
    service_type = service.get_type()

    dispatch_context = FakeDispatchContext()
    dispatch_values = service_type.resolve_service_formulas(service, dispatch_context)
    with pytest.raises(DoesNotExist):
        service_type.dispatch_data(service, dispatch_values, dispatch_context)


@pytest.mark.django_db
def test_local_baserow_get_row_service_dispatch_data_no_row_id(data_fixture):
    user = data_fixture.create_user()
    page = data_fixture.create_builder_page(user=user)
    table, fields, rows = data_fixture.build_table(
        user=user,
        columns=[
            ("Name", "text"),
            ("Email", "text"),
        ],
        rows=[
            ["Ada Lovelace", "ada@baserow.io"],
            ["Blaise Pascal", "blaise@baserow.io"],
        ],
    )
    integration = data_fixture.create_local_baserow_integration(
        application=page.builder, user=user
    )

    service = data_fixture.create_local_baserow_get_row_service(
        integration=integration, table=table, row_id=""
    )
    service_type = service.get_type()

    dispatch_context = FakeDispatchContext()
    dispatch_values = service_type.resolve_service_formulas(service, dispatch_context)
    dispatch_data = service_type.dispatch_data(
        service, dispatch_values, dispatch_context
    )

    assert dispatch_data["data"].id == rows[0].id

    # If the `row_id` is a formula, and its resolved value is blank, ensure we're
    # raising `ServiceImproperlyConfigured`. We don't want to use the "no row ID"
    # behaviour of returning the first row if we're using formulas.
    fake_request = Mock()
    fake_request.data = {"page_parameter": {"id": ""}}
    service.row_id = 'get("page_parameter.id")'
    dispatch_context = BuilderDispatchContext(fake_request, page)
    with pytest.raises(ServiceImproperlyConfigured) as exc:
        service_type.resolve_service_formulas(service, dispatch_context)

    assert (
        exc.value.args[0] == "The result of the `row_id` formula must "
        "be an integer or convertible to an integer."
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

    view = data_fixture.create_grid_view(user, table=table, owned_by=user)
    data_fixture.create_view_filter(view=view, field=field, type="contains", value="Ch")

    service_type = LocalBaserowListRowsUserServiceType()
    service = data_fixture.create_local_baserow_list_rows_service(
        view=view, table=table, integration=integration
    )

    dispatch_context = FakeDispatchContext()
    dispatch_values = service_type.resolve_service_formulas(service, dispatch_context)
    dispatch_data = service_type.dispatch_data(
        service, dispatch_values, dispatch_context
    )
    results = dispatch_data["results"]
    assert [r.id for r in results] == [row_1.id, row_2.id]

    data_fixture.create_local_baserow_table_service_filter(
        service=service,
        field=field,
        value="'Cheese'",
        order=0,
        value_is_formula=True,
    )

    dispatch_values = service_type.resolve_service_formulas(service, dispatch_context)
    dispatch_data = service_type.dispatch_data(
        service, dispatch_values, dispatch_context
    )
    results = dispatch_data["results"]
    assert [r.id for r in results] == [row_1.id]


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
        user, table=table, owned_by=user, filter_type="OR"
    )
    dispatch_context = FakeDispatchContext()
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
        service=service, field=cost, value="'150'", order=0, value_is_formula=True
    )
    dispatch_values = service_type.resolve_service_formulas(service, dispatch_context)
    dispatch_data = service_type.dispatch_data(
        service, dispatch_values, dispatch_context
    )
    results = dispatch_data["results"]
    assert [r.id for r in results] == [
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
        service=service, field=cost, value="'25'", order=0, value_is_formula=True
    )
    data_fixture.create_local_baserow_table_service_filter(
        service=service, field=cost, value="'50'", order=0, value_is_formula=True
    )
    dispatch_values = service_type.resolve_service_formulas(service, dispatch_context)
    dispatch_data = service_type.dispatch_data(
        service, dispatch_values, dispatch_context
    )
    results = dispatch_data["results"]
    assert [r.id for r in results] == [
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
    view = data_fixture.create_grid_view(user, table=table, owned_by=user)
    service_type = LocalBaserowListRowsUserServiceType()
    service = data_fixture.create_local_baserow_list_rows_service(
        view=view, table=table, integration=integration
    )

    dispatch_context = FakeDispatchContext()
    dispatch_values = service_type.resolve_service_formulas(service, dispatch_context)

    # A `ViewSort` alone.
    view_sort = data_fixture.create_view_sort(view=view, field=ingredients, order="ASC")
    dispatch_data = service_type.dispatch_data(
        service, dispatch_values, dispatch_context
    )
    results = dispatch_data["results"]
    assert [r.id for r in results] == [
        row_3.id,
        row_1.id,
        row_2.id,
    ]
    view_sort.delete()

    # A `ServiceSort` alone.
    service_sort = data_fixture.create_local_baserow_table_service_sort(
        service=service, field=cost, order_by=SORT_ORDER_DESC, order=0
    )
    dispatch_values = service_type.resolve_service_formulas(service, dispatch_context)
    dispatch_data = service_type.dispatch_data(
        service, dispatch_values, dispatch_context
    )
    results = dispatch_data["results"]
    assert [r.id for r in results] == [
        row_3.id,
        row_2.id,
        row_1.id,
    ]
    service_sort.delete()

    # A `ViewSort` & `ServiceSort`, the latter is used.
    data_fixture.create_local_baserow_table_service_sort(
        service=service, field=cost, order_by=SORT_ORDER_ASC, order=0
    )
    data_fixture.create_view_sort(view=view, field=cost, order=SORT_ORDER_DESC)
    dispatch_values = service_type.resolve_service_formulas(service, dispatch_context)
    dispatch_data = service_type.dispatch_data(
        service, dispatch_values, dispatch_context
    )
    results = dispatch_data["results"]
    assert [r.id for r in results] == [
        row_1.id,
        row_2.id,
        row_3.id,
    ]


@pytest.mark.django_db
def test_local_baserow_list_rows_service_dispatch_data_with_pagination(
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
    RowHandler().create_rows(
        user,
        table,
        rows_values=[
            {f"field_{field.id}": "Cheese"},
            {f"field_{field.id}": "Chicken"},
            {f"field_{field.id}": "Milk"},
            {f"field_{field.id}": "Salt"},
            {f"field_{field.id}": "Pepper"},
            {f"field_{field.id}": "Tomato"},
            {f"field_{field.id}": "Potato"},
            {f"field_{field.id}": "Cucumber"},
            {f"field_{field.id}": "Rice"},
            {f"field_{field.id}": "Beans"},
        ],
    )

    service_type = LocalBaserowListRowsUserServiceType()
    service = data_fixture.create_local_baserow_list_rows_service(
        table=table, integration=integration
    )

    dispatch_data = service_type.dispatch_data(
        service, {"table": table}, FakeDispatchContext()
    )

    assert len(dispatch_data["results"]) == 10
    assert dispatch_data["has_next_page"] is False

    fake_dispatch = FakeDispatchContext()

    fake_dispatch.range = Mock()
    fake_dispatch.range.return_value = [0, 5]

    dispatch_data = service_type.dispatch_data(service, {"table": table}, fake_dispatch)

    assert len(dispatch_data["results"]) == 5
    assert dispatch_data["has_next_page"] is True

    fake_dispatch.range.return_value = [5, 3]

    dispatch_data = service_type.dispatch_data(service, {"table": table}, fake_dispatch)

    assert len(dispatch_data["results"]) == 3
    assert dispatch_data["has_next_page"] is True

    fake_dispatch.range.return_value = [5, 5]

    dispatch_data = service_type.dispatch_data(service, {"table": table}, fake_dispatch)

    assert len(dispatch_data["results"]) == 5
    assert dispatch_data["has_next_page"] is False

    fake_dispatch.range.return_value = [5, 10]

    dispatch_data = service_type.dispatch_data(service, {"table": table}, fake_dispatch)

    assert len(dispatch_data["results"]) == 5
    assert dispatch_data["has_next_page"] is False


@pytest.mark.django_db
def test_local_baserow_table_service_before_dispatch_validation_error(
    data_fixture,
):
    cls = LocalBaserowTableServiceType
    cls.model_class = Mock()

    user = data_fixture.create_user()
    workspace = data_fixture.create_workspace(user=user)
    database = data_fixture.create_database_application(workspace=workspace)
    trashed_table = data_fixture.create_database_table(
        user, database=database, trashed=True
    )
    trashed_database = data_fixture.create_database_application(
        workspace=workspace, trashed=True
    )
    table_in_trashed_database = data_fixture.create_database_table(
        user, database=trashed_database
    )

    service_without_table = Mock(table_id=None)
    with pytest.raises(ServiceImproperlyConfigured) as exc:
        cls().resolve_service_formulas(service_without_table, FakeDispatchContext())
    assert exc.value.args[0] == "The table property is missing."

    service_with_trashed_table = Mock(table_id=trashed_table.id)
    with pytest.raises(ServiceImproperlyConfigured) as exc:
        cls().resolve_service_formulas(
            service_with_trashed_table, FakeDispatchContext()
        )
    assert exc.value.args[0] == "The specified table is trashed"

    service_with_table_in_trashed_database = Mock(table_id=table_in_trashed_database.id)
    with pytest.raises(ServiceImproperlyConfigured) as exc:
        cls().resolve_service_formulas(
            service_with_table_in_trashed_database, FakeDispatchContext()
        )
    assert exc.value.args[0] == "The specified table is trashed"


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
    table, _, _, _, _ = setup_interesting_test_table(
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
        field_db_column_by_name["last_modified_by"]: {
            "default": None,
            "metadata": {},
            "original_type": "last_modified_by",
            "properties": {
                "id": {"title": "id", "type": "number"},
                "name": {"title": "name", "type": "string"},
            },
            "title": "last_modified_by",
            "type": "object",
        },
        field_db_column_by_name["created_by"]: {
            "default": None,
            "metadata": {},
            "original_type": "created_by",
            "properties": {
                "id": {"title": "id", "type": "number"},
                "name": {"title": "name", "type": "string"},
            },
            "title": "created_by",
            "type": "object",
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
        field_db_column_by_name["formula_multipleselect"]: {
            "title": "formula_multipleselect",
            "default": None,
            "original_type": "formula",
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
        field_db_column_by_name["uuid"]: {
            "title": "uuid",
            "default": None,
            "original_type": "uuid",
            "metadata": {},
            "type": "string",
        },
        field_db_column_by_name["autonumber"]: {
            "title": "autonumber",
            "default": None,
            "original_type": "autonumber",
            "metadata": {},
            "type": "number",
        },
        field_db_column_by_name["duration_hm"]: {
            "title": "duration_hm",
            "default": None,
            "original_type": "duration",
            "metadata": {},
            "type": "string",
        },
        field_db_column_by_name["duration_hms"]: {
            "title": "duration_hms",
            "default": None,
            "original_type": "duration",
            "metadata": {},
            "type": "string",
        },
        field_db_column_by_name["duration_hms_s"]: {
            "title": "duration_hms_s",
            "default": None,
            "original_type": "duration",
            "metadata": {},
            "type": "string",
        },
        field_db_column_by_name["duration_hms_ss"]: {
            "title": "duration_hms_ss",
            "default": None,
            "original_type": "duration",
            "metadata": {},
            "type": "string",
        },
        field_db_column_by_name["duration_hms_sss"]: {
            "title": "duration_hms_sss",
            "default": None,
            "original_type": "duration",
            "metadata": {},
            "type": "string",
        },
        field_db_column_by_name["duration_dh"]: {
            "title": "duration_dh",
            "default": None,
            "original_type": "duration",
            "metadata": {},
            "type": "string",
        },
        field_db_column_by_name["duration_dhm"]: {
            "title": "duration_dhm",
            "default": None,
            "original_type": "duration",
            "metadata": {},
            "type": "string",
        },
        field_db_column_by_name["duration_dhms"]: {
            "title": "duration_dhms",
            "default": None,
            "original_type": "duration",
            "metadata": {},
            "type": "string",
        },
        field_db_column_by_name["password"]: {
            "title": "password",
            "default": None,
            "original_type": "password",
            "metadata": {},
            "type": "boolean",
        },
        "id": {"metadata": {}, "type": "number", "title": "Id"},
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


def test_local_baserow_table_service_type_after_update_table_change_deletes_filters_and_sorts():
    mock_instance = Mock()
    mock_from_table = Mock()
    mock_to_table = Mock()
    change_table_from_Table_to_None = {"table": (mock_from_table, None)}
    change_table_from_None_to_Table = {"table": (None, mock_to_table)}
    change_table_from_Table_to_Table = {"table": (mock_from_table, mock_to_table)}

    service_type_cls = LocalBaserowTableServiceType
    service_type_cls.model_class = Mock()
    service_type = service_type_cls()

    service_type.after_update(mock_instance, {}, change_table_from_Table_to_None)
    assert not mock_instance.service_filters.all.return_value.delete.called
    assert not mock_instance.service_sorts.all.return_value.delete.called

    service_type.after_update(mock_instance, {}, change_table_from_None_to_Table)
    assert not mock_instance.service_filters.all.return_value.delete.called
    assert not mock_instance.service_sorts.all.return_value.delete.called

    service_type.after_update(mock_instance, {}, change_table_from_Table_to_Table)
    assert mock_instance.service_filters.all.return_value.delete.called
    assert mock_instance.service_sorts.all.return_value.delete.called


@pytest.mark.django_db
def test_local_baserow_upsert_row_service_dispatch_data_without_row_id(
    data_fixture,
):
    user = data_fixture.create_user()
    page = data_fixture.create_builder_page(user=user)
    integration = data_fixture.create_local_baserow_integration(
        application=page.builder, user=user
    )
    database = data_fixture.create_database_application(
        workspace=page.builder.workspace
    )
    table = TableHandler().create_table_and_fields(
        user=user,
        database=database,
        name=data_fixture.fake.name(),
        fields=[
            ("Ingredient", "text", {}),
        ],
    )
    ingredient = table.field_set.get(name="Ingredient")

    service = data_fixture.create_local_baserow_upsert_row_service(
        integration=integration,
        table=table,
    )
    service_type = service.get_type()
    service.field_mappings.create(field=ingredient, value='get("page_parameter.id")')

    fake_request = Mock()
    fake_request.data = {"page_parameter": {"id": 2}}

    dispatch_context = BuilderDispatchContext(fake_request, page)
    dispatch_values = service_type.resolve_service_formulas(service, dispatch_context)
    dispatch_data = service_type.dispatch_data(
        service, dispatch_values, dispatch_context
    )

    assert getattr(dispatch_data["data"], ingredient.db_column) == str(
        fake_request.data["page_parameter"]["id"]
    )


@pytest.mark.django_db
def test_local_baserow_upsert_row_service_dispatch_data_with_row_id(
    data_fixture,
):
    user = data_fixture.create_user()
    page = data_fixture.create_builder_page(user=user)
    integration = data_fixture.create_local_baserow_integration(
        application=page.builder, user=user
    )
    database = data_fixture.create_database_application(
        workspace=page.builder.workspace
    )
    table = TableHandler().create_table_and_fields(
        user=user,
        database=database,
        name=data_fixture.fake.name(),
        fields=[
            ("Cost", "number", {}),
        ],
    )
    cost = table.field_set.get(name="Cost")
    row = RowHandler().create_row(
        user=user,
        table=table,
        values={f"field_{cost.id}": 5},
    )

    service = data_fixture.create_local_baserow_upsert_row_service(
        table=table,
        row_id=f"'{row.id}'",
        integration=integration,
    )
    service_type = service.get_type()
    service.field_mappings.create(field=cost, value='get("page_parameter.id")')

    fake_request = Mock()
    fake_request.data = {"page_parameter": {"id": 10}}

    dispatch_context = BuilderDispatchContext(fake_request, page)
    dispatch_values = service_type.resolve_service_formulas(service, dispatch_context)
    dispatch_data = service_type.dispatch_data(
        service, dispatch_values, dispatch_context
    )

    assert (
        getattr(dispatch_data["data"], cost.db_column)
        == fake_request.data["page_parameter"]["id"]
    )

    row.refresh_from_db()
    assert getattr(row, cost.db_column) == fake_request.data["page_parameter"]["id"]


@pytest.mark.django_db
def test_local_baserow_upsert_row_service_dispatch_transform(
    data_fixture,
):
    user = data_fixture.create_user()
    page = data_fixture.create_builder_page(user=user)
    integration = data_fixture.create_local_baserow_integration(
        application=page.builder, user=user
    )
    database = data_fixture.create_database_application(
        workspace=page.builder.workspace
    )
    table = TableHandler().create_table_and_fields(
        user=user,
        database=database,
        name=data_fixture.fake.name(),
        fields=[
            ("Ingredient", "text", {}),
        ],
    )
    ingredient = table.field_set.get(name="Ingredient")

    service = data_fixture.create_local_baserow_upsert_row_service(
        integration=integration,
        table=table,
    )
    service_type = service.get_type()
    service.field_mappings.create(field=ingredient, value='get("page_parameter.id")')

    fake_request = Mock()
    fake_request.data = {"page_parameter": {"id": 2}}

    dispatch_context = BuilderDispatchContext(fake_request, page)
    dispatch_values = service_type.resolve_service_formulas(service, dispatch_context)
    dispatch_data = service_type.dispatch_data(
        service, dispatch_values, dispatch_context
    )

    serialized_row = service_type.dispatch_transform(dispatch_data)
    assert dict(serialized_row) == {
        "id": dispatch_data["data"].id,
        "order": "1.00000000000000000000",
        ingredient.db_column: str(fake_request.data["page_parameter"]["id"]),
    }


@pytest.mark.django_db
def test_local_baserow_upsert_row_service_dispatch_data_incompatible_value(
    data_fixture,
):
    user = data_fixture.create_user()
    page = data_fixture.create_builder_page(user=user)
    integration = data_fixture.create_local_baserow_integration(
        application=page.builder, user=user
    )
    database = data_fixture.create_database_application(
        workspace=page.builder.workspace
    )
    table = TableHandler().create_table_and_fields(
        user=user,
        database=database,
        name=data_fixture.fake.name(),
        fields=[
            ("Active", "boolean", {}),
        ],
    )
    boolean_field = table.field_set.get()
    single_field = FieldHandler().create_field(
        user=user,
        table=table,
        name="Single Select",
        type_name="single_select",
        select_options=[
            {"value": "Option 1", "color": "blue"},
        ],
    )
    service = data_fixture.create_local_baserow_upsert_row_service(
        table=table,
        integration=integration,
    )
    service_type = service.get_type()
    dispatch_context = BuilderDispatchContext(Mock(), page)

    service.field_mappings.create(field=boolean_field, value="'Horse'")
    with pytest.raises(DRFValidationError) as exc:
        service_type.dispatch_data(service, {"table": table}, dispatch_context)

    service.field_mappings.all().delete()

    service.field_mappings.create(field=single_field, value="'99999999999'")
    with pytest.raises(ServiceImproperlyConfigured) as exc:
        service_type.dispatch_data(service, {"table": table}, dispatch_context)

    assert exc.value.args[0] == (
        "The result value of the formula is not valid for the "
        f"field `{single_field.name} ({single_field.db_column})`: "
        "The provided select option value '99999999999' is not a valid select option."
    )


@pytest.mark.django_db
def test_local_baserow_upsert_row_service_resolve_service_formulas(
    data_fixture,
):
    user = data_fixture.create_user()
    page = data_fixture.create_builder_page(user=user)
    integration = data_fixture.create_local_baserow_integration(
        application=page.builder, user=user
    )
    database = data_fixture.create_database_application(
        workspace=page.builder.workspace
    )
    table = TableHandler().create_table_and_fields(
        user=user,
        database=database,
        name=data_fixture.fake.name(),
        fields=[
            ("Name", "text", {}),
        ],
    )
    service = data_fixture.create_local_baserow_upsert_row_service(
        table=table,
        integration=integration,
    )
    service_type = service.get_type()

    dispatch_context = BuilderDispatchContext(Mock(), page)

    # We're creating a row.
    assert service.row_id == ""
    assert service_type.resolve_service_formulas(service, dispatch_context) == {
        "row_id": "",
        "table": table,
    }

    # We're updating a row, but the ID isn't an integer
    service.row_id = "'horse'"
    with pytest.raises(ServiceImproperlyConfigured) as exc:
        service_type.resolve_service_formulas(service, dispatch_context)

    assert exc.value.args[0] == (
        "The result of the `row_id` formula must "
        "be an integer or convertible to an integer."
    )

    # We're updating a row, but the ID formula can't be resolved
    service.row_id = "'horse"
    with pytest.raises(ServiceImproperlyConfigured) as exc:
        service_type.resolve_service_formulas(service, dispatch_context)

    assert exc.value.args[0].startswith("The `row_id` formula can't be resolved")


@pytest.mark.django_db
def test_local_baserow_upsert_row_service_prepare_values(data_fixture):
    user = data_fixture.create_user()
    with pytest.raises(ValidationError) as exc:
        LocalBaserowUpsertRowServiceType().prepare_values(
            {"table_id": 9999999999999999}, user
        )
    assert exc.value.args[0] == f"The table with ID 9999999999999999 does not exist."
    with pytest.raises(ValidationError) as exc:
        LocalBaserowUpsertRowServiceType().prepare_values(
            {"integration_id": 9999999999999999}, user
        )
    assert (
        exc.value.args[0] == f"The integration with ID 9999999999999999 does not exist."
    )


@pytest.mark.django_db(transaction=True)
def test_export_import_local_baserow_upsert_row_service(
    data_fixture,
):
    user, token = data_fixture.create_user_and_token()
    workspace = data_fixture.create_workspace(user=user)
    builder = data_fixture.create_builder_application(workspace=workspace, order=2)
    page = data_fixture.create_builder_page(builder=builder)
    element = data_fixture.create_builder_button_element(page=page)
    database = data_fixture.create_database_application(workspace=workspace, order=1)
    table = data_fixture.create_database_table(database=database)
    field = data_fixture.create_text_field(table=table)
    integration = data_fixture.create_local_baserow_integration(application=builder)

    get_row_service = LocalBaserowGetRow.objects.create(integration=integration)
    data_source = DataSourceService().create_data_source(
        user, service_type=get_row_service.get_type(), page=page
    )
    upsert_row_service = data_fixture.create_local_baserow_upsert_row_service(
        integration=integration,
        table=table,
        row_id=f"get('data_source.{data_source.id}.{field.db_column}')",
    )
    upsert_row_service.field_mappings.create(field=field, value=f"'Horse'")

    data_fixture.create_local_baserow_create_row_workflow_action(
        page=page, element=element, event=EventTypes.CLICK, service=upsert_row_service
    )

    config = ImportExportConfig(include_permission_data=False)
    exported_applications = CoreHandler().export_workspace_applications(
        workspace, BytesIO(), config
    )

    imported_workspace = data_fixture.create_workspace(user=user)
    imported_applications, id_mapping = CoreHandler().import_applications_to_workspace(
        imported_workspace, exported_applications, BytesIO(), config, None
    )

    imported_database, imported_builder = imported_applications
    imported_table = imported_database.table_set.get()
    imported_field = imported_table.field_set.get()

    imported_page = imported_builder.page_set.get()
    imported_data_source = imported_page.datasource_set.get()
    imported_integration = imported_builder.integrations.get()
    imported_upsert_row_service = LocalBaserowUpsertRow.objects.get(
        integration=imported_integration
    )
    imported_field_mapping = imported_upsert_row_service.field_mappings.get()

    assert imported_field_mapping.field == imported_field
    assert (
        imported_upsert_row_service.row_id
        == f"get('data_source.{imported_data_source.id}.{imported_field.db_column}')"
    )


@pytest.mark.django_db()
def test_local_baserow_upsert_row_service_after_update(data_fixture):
    user, token = data_fixture.create_user_and_token()
    page = data_fixture.create_builder_page(user=user)
    integration = data_fixture.create_local_baserow_integration(
        application=page.builder
    )
    table = data_fixture.create_database_table()
    service = data_fixture.create_local_baserow_upsert_row_service(
        integration=integration,
        table=table,
    )
    field = data_fixture.create_text_field(table=table)
    LocalBaserowUpsertRowServiceType().after_update(
        service,
        {
            "table_id": table.id,
            "integration_id": integration.id,
            "field_mappings": [{"field_id": field.id, "value": "'Horse'"}],
        },
        {},
    )
    assert service.field_mappings.count() == 1

    with pytest.raises(ValidationError) as exc:
        LocalBaserowUpsertRowServiceType().after_update(
            service,
            {
                "table_id": table.id,
                "field_mappings": [{"value": "'Bread'"}],
            },
            {},
        )
    assert exc.value.args[0] == "A field mapping must have a `field_id`."

    # Changing the table results in the `field_mapping` getting reset.
    table2 = data_fixture.create_database_table()
    service.table = table2
    service.save()

    with pytest.raises(ValidationError) as exc:
        LocalBaserowUpsertRowServiceType().after_update(
            service,
            {
                "field_mappings": [{"field_id": field.id, "value": "'Pony'"}],
            },
            {"table": (table, table2)},
        )
    assert exc.value.args[0] == f"The field with id {field.id} does not exist."
    service.refresh_from_db()
    assert service.table_id == table2.id
    assert service.field_mappings.count() == 0
