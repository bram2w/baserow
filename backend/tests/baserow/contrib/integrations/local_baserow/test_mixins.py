import json
from unittest.mock import Mock

from django.db import transaction

import pytest

from baserow.contrib.database.rows.handler import RowHandler
from baserow.contrib.database.views.models import SORT_ORDER_DESC
from baserow.contrib.database.views.view_filters import ContainsViewFilterType
from baserow.contrib.integrations.local_baserow.mixins import (
    LocalBaserowTableServiceFilterableMixin,
    LocalBaserowTableServiceSearchableMixin,
    LocalBaserowTableServiceSortableMixin,
)
from baserow.contrib.integrations.local_baserow.service_types import (
    LocalBaserowTableServiceType,
)
from baserow.test_utils.pytest_conftest import FakeDispatchContext


def get_test_service_type(mixin_class):
    class FakeServiceType(mixin_class, LocalBaserowTableServiceType):
        model_class = Mock()

    return FakeServiceType()


@pytest.mark.django_db
def test_local_baserow_table_service_filterable_mixin_get_queryset(
    data_fixture,
):
    service_type = get_test_service_type(LocalBaserowTableServiceFilterableMixin)
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    field = data_fixture.create_text_field(name="Names", table=table)
    table_model = table.get_model()
    service = data_fixture.create_local_baserow_list_rows_service(table=table)

    [alessia, alex, alastair, alexandra] = RowHandler().create_rows(
        user,
        table,
        rows_values=[
            {f"field_{field.id}": "Alessia"},
            {f"field_{field.id}": "Alex"},
            {f"field_{field.id}": "Alastair"},
            {f"field_{field.id}": "Alexandra"},
        ],
    )

    dispatch_context = FakeDispatchContext()

    # No filters of any kind.
    assert [
        row.id
        for row in service_type.get_queryset(
            service, table, dispatch_context, table_model
        )
    ] == [alessia.id, alex.id, alastair.id, alexandra.id]

    # Service filter ensures that the name contains "Ale",
    # which matches Alex, Alexandra and Alessia
    data_fixture.create_local_baserow_table_service_filter(
        service=service,
        field=field,
        value="Ale",
        type=ContainsViewFilterType.type,
        value_is_formula=False,
    )

    assert [
        row.id
        for row in service_type.get_queryset(
            service, table, dispatch_context, table_model
        )
    ] == [alessia.id, alex.id, alexandra.id]

    # Adhoc filter ensures that we also filter on "Alexa", which matches Alexandra.
    dispatch_context = Mock()
    dispatch_context.filters.return_value = json.dumps(
        {
            "groups": [],
            "filter_type": "AND",
            "filters": [
                {
                    "field": field.id,
                    "type": ContainsViewFilterType.type,
                    "value": "Alexa",
                }
            ],
        }
    )

    assert [
        row.id
        for row in service_type.get_queryset(
            service, table, dispatch_context, table_model
        )
    ] == [alexandra.id]


@pytest.mark.django_db
def test_local_baserow_table_service_sortable_mixin_get_queryset(
    data_fixture,
):
    service_type = get_test_service_type(LocalBaserowTableServiceSortableMixin)
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    field = data_fixture.create_text_field(name="Names", table=table)
    table_model = table.get_model()
    service = data_fixture.create_local_baserow_list_rows_service(table=table)

    [aardvark, badger, crow, dragonfly] = RowHandler().create_rows(
        user,
        table,
        rows_values=[
            {f"field_{field.id}": "Aardvark"},
            {f"field_{field.id}": "Badger"},
            {f"field_{field.id}": "Crow"},
            {f"field_{field.id}": "Dragonfly"},
        ],
    )

    dispatch_context = FakeDispatchContext()

    # No sorts of any kind.
    assert [
        row.id
        for row in service_type.get_queryset(
            service, table, dispatch_context, table_model
        )
    ] == [aardvark.id, badger.id, crow.id, dragonfly.id]

    # Service sort ensures that the names are sorted DESC.
    data_fixture.create_local_baserow_table_service_sort(
        service=service, field=field, order_by=SORT_ORDER_DESC, order=0
    )

    assert [
        row.id
        for row in service_type.get_queryset(
            service, table, dispatch_context, table_model
        )
    ] == [dragonfly.id, crow.id, badger.id, aardvark.id]

    # Adhoc sort overrides the service sort.
    dispatch_context = Mock()
    dispatch_context.filters.return_value = None
    dispatch_context.sortings.return_value = field.db_column

    assert [
        row.id
        for row in service_type.get_queryset(
            service, table, dispatch_context, table_model
        )
    ] == [aardvark.id, badger.id, crow.id, dragonfly.id]


@pytest.mark.django_db(transaction=True)
def test_local_baserow_table_service_searchable_mixin_get_queryset(
    data_fixture,
):
    service_type = get_test_service_type(LocalBaserowTableServiceSearchableMixin)

    with transaction.atomic():
        user = data_fixture.create_user()
        table = data_fixture.create_database_table(user=user)
        field = data_fixture.create_text_field(name="Names", table=table)
        service = data_fixture.create_local_baserow_list_rows_service(table=table)
        [alessia, alex, alastair, alexandra] = RowHandler().create_rows(
            user,
            table,
            rows_values=[
                {f"field_{field.id}": "Alessia"},
                {f"field_{field.id}": "Alex"},
                {f"field_{field.id}": "Alastair"},
                {f"field_{field.id}": "Alexandra"},
            ],
        )

    table_model = table.get_model()
    dispatch_context = FakeDispatchContext()

    # No search query of any kind.
    assert [
        row.id
        for row in service_type.get_queryset(
            service, table, dispatch_context, table_model
        )
    ] == [alessia.id, alex.id, alastair.id, alexandra.id]

    # Add a service level search query
    service.search_query = "'Ale'"

    assert [
        row.id
        for row in service_type.get_queryset(
            service, table, dispatch_context, table_model
        )
    ] == [alessia.id, alex.id, alexandra.id]

    # Adhoc search queries extend the service search query.
    dispatch_context = Mock()
    dispatch_context.search_query.return_value = "Alexa"

    assert [
        row.id
        for row in service_type.get_queryset(
            service, table, dispatch_context, table_model
        )
    ] == [alexandra.id]
