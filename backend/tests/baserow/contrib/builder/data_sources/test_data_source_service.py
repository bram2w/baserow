from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from baserow.contrib.builder.data_sources.exceptions import (
    DataSourceDoesNotExist,
    DataSourceImproperlyConfigured,
    DataSourceNotInSamePage,
)
from baserow.contrib.builder.data_sources.models import DataSource
from baserow.contrib.builder.data_sources.service import DataSourceService
from baserow.core.exceptions import PermissionException
from baserow.core.services.models import Service
from baserow.core.services.registries import service_type_registry


@pytest.mark.django_db
@patch("baserow.contrib.builder.data_sources.service.data_source_created")
def test_create_data_source(data_source_created_mock, data_fixture):
    user = data_fixture.create_user()
    page = data_fixture.create_builder_page(user=user)
    data_source1 = data_fixture.create_builder_data_source(page=page, order="1.0000")
    data_source3 = data_fixture.create_builder_data_source(page=page, order="2.0000")

    service_type = service_type_registry.get("local_baserow_get_row")

    data_source = DataSourceService().create_data_source(
        user, service_type=service_type, page=page
    )

    last_data_source = DataSource.objects.last()

    # Check it's the last data_source
    assert last_data_source.id == data_source.id

    assert data_source_created_mock.called_with(data_source=data_source, user=user)


@pytest.mark.django_db
def test_create_data_source_before(data_fixture):
    user = data_fixture.create_user()
    page = data_fixture.create_builder_page(user=user)
    data_source1 = data_fixture.create_builder_data_source(page=page, order="1.0000")
    data_source3 = data_fixture.create_builder_data_source(page=page, order="2.0000")

    service_type = service_type_registry.get("local_baserow_get_row")

    data_source2 = DataSourceService().create_data_source(
        user, service_type=service_type, page=page, before=data_source3
    )

    data_sources = DataSource.objects.all()
    assert data_sources[0].id == data_source1.id
    assert data_sources[1].id == data_source2.id
    assert data_sources[2].id == data_source3.id


@pytest.mark.django_db
def test_create_data_source_before_not_same_page(data_fixture):
    user = data_fixture.create_user()
    page = data_fixture.create_builder_page(user=user)
    data_source1 = data_fixture.create_builder_data_source(page=page, order="1.0000")
    data_source3 = data_fixture.create_builder_data_source(order="2.0000")

    service_type = service_type_registry.get("local_baserow_get_row")

    with pytest.raises(DataSourceNotInSamePage):
        DataSourceService().create_data_source(
            user, service_type=service_type, page=page, before=data_source3
        )


@pytest.mark.django_db
def test_get_unique_orders_before_data_source_triggering_full_page_order_reset(
    data_fixture,
):
    user = data_fixture.create_user()
    page = data_fixture.create_builder_page(user=user)
    data_source_1 = data_fixture.create_builder_data_source(
        page=page, order="1.00000000000000000000"
    )
    data_source_2 = data_fixture.create_builder_data_source(
        page=page, order="1.00000000000000001000"
    )
    data_source_3 = data_fixture.create_builder_data_source(
        page=page, order="2.99999999999999999999"
    )
    data_source_4 = data_fixture.create_builder_data_source(
        page=page, order="2.99999999999999999998"
    )

    service_type = service_type_registry.get("local_baserow_get_row")

    data_source_created = DataSourceService().create_data_source(
        user, service_type=service_type, page=page, before=data_source_3
    )

    data_source_1.refresh_from_db()
    data_source_2.refresh_from_db()
    data_source_3.refresh_from_db()
    data_source_4.refresh_from_db()

    assert data_source_1.order == Decimal("1.00000000000000000000")
    assert data_source_2.order == Decimal("2.00000000000000000000")
    assert data_source_4.order == Decimal("3.00000000000000000000")
    assert data_source_3.order == Decimal("4.00000000000000000000")
    assert data_source_created.order == Decimal("3.50000000000000000000")


@pytest.mark.django_db
@patch("baserow.contrib.builder.data_sources.service.data_source_orders_recalculated")
def test_recalculate_full_order(data_source_orders_recalculated_mock, data_fixture):
    user = data_fixture.create_user()
    page = data_fixture.create_builder_page(user=user)
    data_fixture.create_builder_data_source(page=page, order="1.9000")
    data_fixture.create_builder_data_source(page=page, order="3.4000")

    DataSourceService().recalculate_full_orders(user, page)

    assert data_source_orders_recalculated_mock.called_with(page=page, user=user)


@pytest.mark.django_db
def test_create_data_source_permission_denied(data_fixture, stub_check_permissions):
    user = data_fixture.create_user()
    page = data_fixture.create_builder_page(user=user)

    service_type = service_type_registry.get("local_baserow_get_row")

    with stub_check_permissions(raise_permission_denied=True), pytest.raises(
        PermissionException
    ):
        DataSourceService().create_data_source(
            user,
            service_type=service_type,
            page=page,
        )


@pytest.mark.django_db
def test_get_data_source(data_fixture):
    user = data_fixture.create_user()
    data_source = data_fixture.create_builder_data_source(user=user)

    assert (
        DataSourceService().get_data_source(user, data_source.id).id == data_source.id
    )


@pytest.mark.django_db
def test_get_data_source_does_not_exist(data_fixture):
    user = data_fixture.create_user()

    with pytest.raises(DataSourceDoesNotExist):
        assert DataSourceService().get_data_source(user, 0)


@pytest.mark.django_db
def test_get_data_source_permission_denied(data_fixture, stub_check_permissions):
    user = data_fixture.create_user()
    data_source = data_fixture.create_builder_data_source(user=user)

    with stub_check_permissions(raise_permission_denied=True), pytest.raises(
        PermissionException
    ):
        DataSourceService().get_data_source(user, data_source.id)


@pytest.mark.django_db
def test_get_data_sources(data_fixture, stub_check_permissions):
    user = data_fixture.create_user()
    page = data_fixture.create_builder_page(user=user)
    data_source1 = data_fixture.create_builder_local_baserow_get_row_data_source(
        page=page, user=user
    )
    data_source2 = data_fixture.create_builder_local_baserow_get_row_data_source(
        page=page, user=user
    )
    data_source3 = data_fixture.create_builder_local_baserow_list_rows_data_source(
        page=page, user=user
    )

    assert DataSource.objects.count() == 3
    assert Service.objects.count() == 3

    assert [p.id for p in DataSourceService().get_data_sources(user, page)] == [
        data_source1.id,
        data_source2.id,
        data_source3.id,
    ]

    def exclude_data_source_1(
        actor,
        operation_name,
        queryset,
        workspace=None,
        context=None,
        allow_if_template=False,
    ):
        return queryset.exclude(id=data_source1.id)

    with stub_check_permissions() as stub:
        stub.filter_queryset = exclude_data_source_1

        assert [p.id for p in DataSourceService().get_data_sources(user, page)] == [
            data_source2.id,
            data_source3.id,
        ]


@pytest.mark.django_db
@patch("baserow.contrib.builder.data_sources.service.data_source_deleted")
def test_delete_data_source(data_source_deleted_mock, data_fixture):
    user = data_fixture.create_user()
    data_source = data_fixture.create_builder_data_source(user=user)

    DataSourceService().delete_data_source(user, data_source)

    assert data_source_deleted_mock.called_with(
        data_source_id=data_source.id, user=user
    )


@pytest.mark.django_db(transaction=True)
def test_delete_data_source_permission_denied(data_fixture, stub_check_permissions):
    user = data_fixture.create_user()
    data_source = data_fixture.create_builder_data_source(user=user)

    with stub_check_permissions(raise_permission_denied=True), pytest.raises(
        PermissionException
    ):
        DataSourceService().delete_data_source(user, data_source)


@pytest.mark.django_db
@patch("baserow.contrib.builder.data_sources.service.data_source_updated")
def test_update_data_source(data_source_updated_mock, data_fixture):
    user = data_fixture.create_user()
    data_source = data_fixture.create_builder_data_source(user=user)

    data_source_updated = DataSourceService().update_data_source(
        user, data_source, value="newValue"
    )

    assert data_source_updated_mock.called_with(
        data_source=data_source_updated, user=user
    )


@pytest.mark.django_db(transaction=True)
def test_update_data_source_permission_denied(data_fixture, stub_check_permissions):
    user = data_fixture.create_user()
    data_source = data_fixture.create_builder_data_source(user=user)

    with stub_check_permissions(raise_permission_denied=True), pytest.raises(
        PermissionException
    ):
        DataSourceService().update_data_source(user, data_source, value="newValue")


@pytest.mark.django_db
@patch("baserow.contrib.builder.data_sources.service.data_source_updated")
def test_move_data_source(data_source_updated_mock, data_fixture):
    user = data_fixture.create_user()
    page = data_fixture.create_builder_page(user=user)
    data_source1 = data_fixture.create_builder_data_source(page=page)
    data_source2 = data_fixture.create_builder_data_source(page=page)
    data_source3 = data_fixture.create_builder_local_baserow_list_rows_data_source(
        page=page
    )

    data_source_moved = DataSourceService().move_data_source(
        user, data_source3, before=data_source2
    )

    assert data_source_updated_mock.called_with(
        data_source=data_source_moved, user=user
    )


@pytest.mark.django_db
def test_move_data_source_not_same_page(data_fixture, stub_check_permissions):
    user = data_fixture.create_user()
    page = data_fixture.create_builder_page(user=user)
    page2 = data_fixture.create_builder_page(user=user)
    data_source1 = data_fixture.create_builder_data_source(page=page)
    data_source2 = data_fixture.create_builder_data_source(page=page)
    data_source3 = data_fixture.create_builder_local_baserow_list_rows_data_source(
        page=page2
    )

    with pytest.raises(DataSourceNotInSamePage):
        DataSourceService().move_data_source(user, data_source3, before=data_source2)


@pytest.mark.django_db
def test_move_data_source_permission_denied(data_fixture, stub_check_permissions):
    user = data_fixture.create_user()
    page = data_fixture.create_builder_page(user=user)
    data_source1 = data_fixture.create_builder_data_source(page=page)
    data_source2 = data_fixture.create_builder_data_source(page=page)
    data_source3 = data_fixture.create_builder_local_baserow_list_rows_data_source(
        page=page
    )

    with stub_check_permissions(raise_permission_denied=True), pytest.raises(
        PermissionException
    ):
        DataSourceService().move_data_source(user, data_source3, before=data_source2)


@pytest.mark.django_db
@patch("baserow.contrib.builder.data_sources.service.data_source_orders_recalculated")
def test_move_data_source_trigger_order_recalculed(
    data_source_orders_recalculated_mock, data_fixture
):
    user = data_fixture.create_user()
    page = data_fixture.create_builder_page(user=user)
    data_source1 = data_fixture.create_builder_data_source(
        page=page, order="2.99999999999999999998"
    )
    data_source2 = data_fixture.create_builder_data_source(
        page=page, order="2.99999999999999999999"
    )
    data_source3 = data_fixture.create_builder_data_source(page=page, order="3.0000")

    DataSourceService().move_data_source(user, data_source3, before=data_source2)

    assert data_source_orders_recalculated_mock.called_with(page=page, user=user)


@pytest.mark.django_db
def test_dispatch_data_source(data_fixture):
    user = data_fixture.create_user()
    table, fields, rows = data_fixture.build_table(
        user=user,
        columns=[
            ("Name", "text"),
            ("My Color", "text"),
        ],
        rows=[
            ["BMW", "Blue"],
            ["Audi", "Orange"],
            ["Volkswagen", "White"],
            ["Volkswagen", "Green"],
        ],
    )
    builder = data_fixture.create_builder_application(user=user)
    integration = data_fixture.create_local_baserow_integration(
        user=user, application=builder
    )
    page = data_fixture.create_builder_page(user=user, builder=builder)
    data_source = data_fixture.create_builder_local_baserow_get_row_data_source(
        user=user, page=page, integration=integration, table=table, row_id="2"
    )

    formula_context = MagicMock()
    formula_context.cache = {}

    result = DataSourceService().dispatch_data_source(
        user, data_source, formula_context
    )

    assert result == {
        "id": rows[1].id,
        "order": "1.00000000000000000000",
        "Name": "Audi",
        "My Color": "Orange",
    }


@pytest.mark.django_db
def test_dispatch_page_data_sources(data_fixture):
    user = data_fixture.create_user()
    table, fields, rows = data_fixture.build_table(
        user=user,
        columns=[
            ("Name", "text"),
            ("My Color", "text"),
        ],
        rows=[
            ["BMW", "Blue"],
            ["Audi", "Orange"],
            ["Volkswagen", "White"],
            ["Volkswagen", "Green"],
        ],
    )
    builder = data_fixture.create_builder_application(user=user)
    integration = data_fixture.create_local_baserow_integration(
        user=user, application=builder
    )
    page = data_fixture.create_builder_page(user=user, builder=builder)
    data_source = data_fixture.create_builder_local_baserow_get_row_data_source(
        user=user, page=page, integration=integration, table=table, row_id="2"
    )
    data_source2 = data_fixture.create_builder_local_baserow_get_row_data_source(
        user=user, page=page, integration=integration, table=table, row_id="3"
    )
    data_source3 = data_fixture.create_builder_local_baserow_get_row_data_source(
        user=user, page=page, integration=integration, table=table, row_id="b"
    )

    formula_context = MagicMock()
    formula_context.cache = {}

    result = DataSourceService().dispatch_page_data_sources(user, page, formula_context)

    assert result[data_source.id] == {
        "id": rows[1].id,
        "order": "1.00000000000000000000",
        "Name": "Audi",
        "My Color": "Orange",
    }

    assert result[data_source2.id] == {
        "id": rows[2].id,
        "order": "1.00000000000000000000",
        "Name": "Volkswagen",
        "My Color": "White",
    }

    assert isinstance(result[data_source3.id], Exception)


@pytest.mark.django_db
def test_dispatch_data_source_permission_denied(data_fixture, stub_check_permissions):
    user = data_fixture.create_user()
    table, fields, rows = data_fixture.build_table(
        user=user,
        columns=[
            ("Name", "text"),
            ("My Color", "text"),
        ],
        rows=[
            ["BMW", "Blue"],
        ],
    )
    builder = data_fixture.create_builder_application(user=user)
    integration = data_fixture.create_local_baserow_integration(
        user=user, application=builder
    )
    page = data_fixture.create_builder_page(user=user, builder=builder)
    data_source = data_fixture.create_builder_local_baserow_get_row_data_source(
        user=user, page=page, integration=integration, table=table, row_id="1"
    )

    formula_context = MagicMock()
    formula_context.cache = {}

    with stub_check_permissions(raise_permission_denied=True), pytest.raises(
        PermissionException
    ):
        DataSourceService().dispatch_data_source(user, data_source, formula_context)


@pytest.mark.django_db
def test_dispatch_data_source_improperly_configured(data_fixture):
    user = data_fixture.create_user()

    builder = data_fixture.create_builder_application(user=user)
    integration = data_fixture.create_local_baserow_integration(
        user=user, application=builder
    )
    page = data_fixture.create_builder_page(user=user, builder=builder)
    data_source = data_fixture.create_builder_local_baserow_get_row_data_source(
        user=user,
        page=page,
        integration=None,
    )

    # Without type
    data_source = data_fixture.create_builder_data_source(
        user=user, page=page, integration=integration
    )

    formula_context = MagicMock()
    formula_context.cache = {}

    with pytest.raises(DataSourceImproperlyConfigured):
        DataSourceService().dispatch_data_source(user, data_source, formula_context)
