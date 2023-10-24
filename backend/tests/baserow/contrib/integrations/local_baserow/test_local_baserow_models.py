import pytest

from baserow.contrib.database.table.handler import TableHandler
from baserow.contrib.database.views.models import SORT_ORDER_DESC
from baserow.contrib.integrations.local_baserow.models import (
    LocalBaserowTableServiceFilter,
    LocalBaserowTableServiceSort,
)


@pytest.mark.django_db
def test_local_baserow_table_service_refinement_manager(data_fixture):
    user = data_fixture.create_user()
    builder = data_fixture.create_builder_application(user=user)
    database = data_fixture.create_database_application(workspace=builder.workspace)
    integration = data_fixture.create_local_baserow_integration(
        application=builder, user=user
    )
    table = TableHandler().create_table_and_fields(
        user=user,
        database=database,
        name=data_fixture.fake.name(),
        fields=[
            ("Ingredient", "text", {}),
            ("Cost", "number", {}),
        ],
    )

    service = data_fixture.create_local_baserow_list_rows_service(
        table=table, integration=integration
    )

    cost = table.field_set.get(name="Cost")
    ingredient = table.field_set.get(name="Ingredient")

    data_fixture.create_local_baserow_table_service_filter(
        service=service, field=cost, value="25", order=0
    )
    data_fixture.create_local_baserow_table_service_filter(
        service=service, field=ingredient, value="Cheese", order=1
    )

    data_fixture.create_local_baserow_table_service_sort(
        service=service, field=cost, order_by=SORT_ORDER_DESC, order=0
    )
    data_fixture.create_local_baserow_table_service_sort(
        service=service, field=ingredient, order_by=SORT_ORDER_DESC, order=1
    )

    ingredient.trashed = True
    ingredient.save()

    assert LocalBaserowTableServiceFilter.objects.filter(service=service).count() == 1
    assert (
        LocalBaserowTableServiceFilter.objects_and_trash.filter(service=service).count()
        == 2
    )

    assert LocalBaserowTableServiceSort.objects.filter(service=service).count() == 1
    assert (
        LocalBaserowTableServiceSort.objects_and_trash.filter(service=service).count()
        == 2
    )
