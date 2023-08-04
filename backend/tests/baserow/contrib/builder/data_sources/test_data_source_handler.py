from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from baserow.contrib.builder.data_sources.exceptions import DataSourceDoesNotExist
from baserow.contrib.builder.data_sources.handler import DataSourceHandler
from baserow.contrib.builder.data_sources.models import DataSource
from baserow.contrib.integrations.local_baserow.models import (
    LocalBaserowGetRow,
    LocalBaserowListRows,
)
from baserow.core.exceptions import CannotCalculateIntermediateOrder
from baserow.core.services.registries import service_type_registry


@pytest.mark.django_db
def test_create_data_source(data_fixture):
    page = data_fixture.create_builder_page()

    service_type = service_type_registry.get("local_baserow_get_row")

    data_source = DataSourceHandler().create_data_source(page=page, name="Data source")

    assert data_source.page.id == page.id

    assert data_source.order == 1
    assert DataSource.objects.count() == 1

    data_source = DataSourceHandler().create_data_source(
        page=page, name="Data source 1", service_type=service_type
    )

    assert data_source.order == 2
    assert isinstance(data_source.service, LocalBaserowGetRow)
    assert data_source.name == "Data source 1"
    assert DataSource.objects.count() == 2


@pytest.mark.django_db
def test_get_data_source(data_fixture):
    data_source = data_fixture.create_builder_local_baserow_get_row_data_source()
    assert DataSourceHandler().get_data_source(data_source.id).id == data_source.id


@pytest.mark.django_db
def test_get_data_source_does_not_exist(data_fixture):
    with pytest.raises(DataSourceDoesNotExist):
        assert DataSourceHandler().get_data_source(0)


@pytest.mark.django_db
def test_get_data_sources(data_fixture):
    page = data_fixture.create_builder_page()
    data_source1 = data_fixture.create_builder_local_baserow_get_row_data_source(
        page=page
    )
    data_source2 = data_fixture.create_builder_local_baserow_get_row_data_source(
        page=page
    )
    data_source3 = data_fixture.create_builder_local_baserow_list_rows_data_source(
        page=page
    )
    data_source4 = data_fixture.create_builder_data_source(page=page)

    data_sources = DataSourceHandler().get_data_sources(page)

    assert [e.id for e in data_sources] == [
        data_source1.id,
        data_source2.id,
        data_source3.id,
        data_source4.id,
    ]

    assert isinstance(data_sources[0].service, LocalBaserowGetRow)
    assert isinstance(data_sources[2].service, LocalBaserowListRows)
    assert data_sources[3].service is None


@pytest.mark.django_db
def test_delete_data_source(data_fixture):
    data_source = data_fixture.create_builder_local_baserow_get_row_data_source()

    DataSourceHandler().delete_data_source(data_source)

    assert DataSource.objects.count() == 0


@pytest.mark.django_db
def test_update_data_source(data_fixture):
    user = data_fixture.create_user()
    data_source = data_fixture.create_builder_local_baserow_get_row_data_source(
        user=user
    )

    service_type = service_type_registry.get("local_baserow_get_row")

    data_source_updated = DataSourceHandler().update_data_source(
        data_source, service_type, name="newValue"
    )

    assert data_source_updated.name == "newValue"


@pytest.mark.django_db
def test_update_data_source_change_type(data_fixture):
    user = data_fixture.create_user()
    data_source = data_fixture.create_builder_local_baserow_get_row_data_source(
        user=user
    )

    service_type = service_type_registry.get("local_baserow_get_row")
    new_service_type = service_type_registry.get("local_baserow_list_rows")

    data_source_updated = DataSourceHandler().update_data_source(
        data_source, service_type, new_service_type=new_service_type
    )

    assert (
        service_type_registry.get_by_model(data_source_updated.service).type
        == "local_baserow_list_rows"
    )

    data_source_updated = DataSourceHandler().update_data_source(
        data_source, service_type, new_service_type=None
    )

    assert data_source_updated.service is None


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
    MagicMock.cache = {}

    result = DataSourceHandler().dispatch_data_source(data_source, formula_context)

    assert result == {
        "id": rows[1].id,
        "order": "1.00000000000000000000",
        "Name": "Audi",
        "My Color": "Orange",
    }


@pytest.mark.django_db
def test_dispatch_data_sources(data_fixture):
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
    MagicMock.cache = {}

    result = DataSourceHandler().dispatch_data_sources(
        [data_source, data_source2, data_source3], formula_context
    )

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
def test_update_data_source_invalid_values(data_fixture):
    data_source = data_fixture.create_builder_local_baserow_get_row_data_source()

    service_type = service_type_registry.get("local_baserow_get_row")

    data_source_updated = DataSourceHandler().update_data_source(
        data_source, service_type=service_type, nonsense="hello"
    )

    assert not hasattr(data_source_updated, "nonsense")


@pytest.mark.django_db
def test_move_data_source_end_of_page(data_fixture):
    page = data_fixture.create_builder_page()
    data_source1 = data_fixture.create_builder_local_baserow_get_row_data_source(
        page=page
    )
    data_source2 = data_fixture.create_builder_local_baserow_get_row_data_source(
        page=page
    )
    data_source3 = data_fixture.create_builder_local_baserow_get_row_data_source(
        page=page
    )

    data_source_moved = DataSourceHandler().move_data_source(data_source1)

    assert DataSource.objects.filter(page=page).last().id == data_source_moved.id


@pytest.mark.django_db
def test_move_data_source_before(data_fixture):
    page = data_fixture.create_builder_page()
    data_source1 = data_fixture.create_builder_local_baserow_get_row_data_source(
        page=page
    )
    data_source2 = data_fixture.create_builder_local_baserow_get_row_data_source(
        page=page
    )
    data_source3 = data_fixture.create_builder_local_baserow_get_row_data_source(
        page=page
    )

    DataSourceHandler().move_data_source(data_source3, before=data_source2)

    assert [e.id for e in DataSource.objects.filter(page=page).all()] == [
        data_source1.id,
        data_source3.id,
        data_source2.id,
    ]


@pytest.mark.django_db
def test_move_data_source_before_fails(data_fixture):
    page = data_fixture.create_builder_page()
    data_source1 = data_fixture.create_builder_local_baserow_get_row_data_source(
        page=page, order="2.99999999999999999998"
    )
    data_source2 = data_fixture.create_builder_local_baserow_get_row_data_source(
        page=page, order="2.99999999999999999999"
    )
    data_source3 = data_fixture.create_builder_local_baserow_get_row_data_source(
        page=page, order="3.0000"
    )

    with pytest.raises(CannotCalculateIntermediateOrder):
        DataSourceHandler().move_data_source(data_source3, before=data_source2)


@pytest.mark.django_db
def test_recalculate_full_orders(data_fixture):
    page = data_fixture.create_builder_page()
    data_source1 = data_fixture.create_builder_local_baserow_get_row_data_source(
        page=page, order="1.99999999999999999999"
    )
    data_source2 = data_fixture.create_builder_local_baserow_get_row_data_source(
        page=page, order="2.00000000000000000000"
    )
    data_source3 = data_fixture.create_builder_local_baserow_get_row_data_source(
        page=page, order="1.99999999999999999999"
    )
    data_source4 = data_fixture.create_builder_local_baserow_get_row_data_source(
        page=page, order="2.10000000000000000000"
    )
    data_source5 = data_fixture.create_builder_local_baserow_get_row_data_source(
        page=page, order="3.00000000000000000000"
    )
    data_source6 = data_fixture.create_builder_local_baserow_get_row_data_source(
        page=page, order="1.00000000000000000001"
    )
    data_source7 = data_fixture.create_builder_local_baserow_get_row_data_source(
        page=page, order="3.99999999999999999999"
    )
    data_source8 = data_fixture.create_builder_local_baserow_get_row_data_source(
        page=page, order="4.00000000000000000001"
    )

    page2 = data_fixture.create_builder_page()

    data_sourceA = data_fixture.create_builder_local_baserow_get_row_data_source(
        page=page2, order="1.99999999999999999999"
    )
    data_sourceB = data_fixture.create_builder_local_baserow_get_row_data_source(
        page=page2, order="2.00300000000000000000"
    )

    DataSourceHandler().recalculate_full_orders(page)

    data_sources = DataSource.objects.filter(page=page)
    assert data_sources[0].id == data_source6.id
    assert data_sources[0].order == Decimal("1.00000000000000000000")

    assert data_sources[1].id == data_source1.id
    assert data_sources[1].order == Decimal("2.00000000000000000000")

    assert data_sources[2].id == data_source3.id
    assert data_sources[2].order == Decimal("3.00000000000000000000")

    assert data_sources[3].id == data_source2.id
    assert data_sources[3].order == Decimal("4.00000000000000000000")

    assert data_sources[4].id == data_source4.id
    assert data_sources[4].order == Decimal("5.00000000000000000000")

    assert data_sources[5].id == data_source5.id
    assert data_sources[5].order == Decimal("6.00000000000000000000")

    assert data_sources[6].id == data_source7.id
    assert data_sources[6].order == Decimal("7.00000000000000000000")

    assert data_sources[7].id == data_source8.id
    assert data_sources[7].order == Decimal("8.00000000000000000000")

    # Other page data_sources shouldn't be reordered
    data_sources = DataSource.objects.filter(page=page2)
    assert data_sources[0].id == data_sourceA.id
    assert data_sources[0].order == Decimal("1.99999999999999999999")

    assert data_sources[1].id == data_sourceB.id
    assert data_sources[1].order == Decimal("2.00300000000000000000")
