from decimal import Decimal

import pytest
from django.urls import reverse
from pyinstrument import Profiler
from rest_framework.status import HTTP_200_OK

from baserow.contrib.database.fields.handler import FieldHandler
from baserow.contrib.database.management.commands.fill_table import fill_table
from baserow.contrib.database.rows.handler import RowHandler
from baserow.core.trash.handler import TrashHandler
from tests.test_utils import setup_interesting_test_table


@pytest.mark.django_db
@pytest.mark.slow
# You must add --runslow -s to pytest to run this test, you can do this in intellij by
# editing the run config for this test and adding --runslow -s to additional args.
def test_adding_a_formula_field_compared_to_normal_field_isnt_slow(data_fixture):

    table, user, row, _ = setup_interesting_test_table(data_fixture)
    count = 1000
    fill_table(count, table)

    profiler = Profiler()
    profiler.start()
    field = FieldHandler().create_field(
        user=user, table=table, name="perf_formula", type_name="formula", formula="'1'"
    )
    profiler.stop()
    print("--------- Adding a formula field! -------")
    print(profiler.output_text(unicode=True, color=True))

    TrashHandler.permanently_delete(field)

    profiler = Profiler()
    profiler.start()
    FieldHandler().create_field(
        user=user, table=table, name="perf_text", type_name="text"
    )
    profiler.stop()
    print("--------- Adding a normal field! -------")
    print(profiler.output_text(unicode=True, color=True))


@pytest.mark.django_db
@pytest.mark.slow
# You must add --runslow -s to pytest to run this test, you can do this in intellij by
# editing the run config for this test and adding --runslow -s to additional args.
def test_very_nested_formula_field_change(data_fixture, django_assert_num_queries):

    user = data_fixture.create_user()
    table, fields, rows = data_fixture.build_table(
        columns=[("number", "number")], rows=[["0"]], user=user
    )

    FieldHandler().create_field(
        user=user,
        table=table,
        name=f"perf_formula0",
        type_name="formula",
        formula="field('number')+1",
    )

    # Create many formulas each referencing the field next to them and adding on one
    last_field = None
    num_formulas = 200
    for i in range(1, num_formulas):
        print(f"Creating formula {i}")
        last_field = FieldHandler().create_field(
            user=user,
            table=table,
            name=f"perf_formula{i}",
            type_name="formula",
            formula=f"field('perf_formula{i-1}')+1",
        )
    profiler = Profiler()
    profiler.start()
    # with django_assert_num_queries(1):
    table.get_model()
    created_row = RowHandler().create_row(user, table, {f"field_{fields[0].id}": 0})
    assert getattr(created_row, f"field_{last_field.id}") == Decimal(num_formulas)
    profiler.stop()
    print(profiler.output_text(unicode=True, color=True))


@pytest.mark.django_db
@pytest.mark.slow
# You must add --runslow -s to pytest to run this test, you can do this in intellij by
# editing the run config for this test and adding --runslow -s to additional args.
def test_creating_very_nested_formula_field(data_fixture):

    user = data_fixture.create_user()
    table, fields, rows = data_fixture.build_table(
        columns=[("perf_formula0", "number")], rows=[["0"]], user=user
    )
    fill_table(10000, table)
    num_formulas = 100
    profiler = Profiler()
    profiler.start()
    for i in range(1, num_formulas):
        print(f"Making formula field {i}")
        FieldHandler().create_field(
            user=user,
            table=table,
            name=f"perf_formula{i}",
            type_name="formula",
            formula=f"field('perf_formula{i-1}')+1",
        )
    profiler.stop()
    print(profiler.output_text(unicode=True, color=True))


@pytest.mark.django_db
@pytest.mark.slow
# You must add --runslow -s to pytest to run this test, you can do this in intellij by
# editing the run config for this test and adding --runslow -s to additional args.
def test_altering_very_nested_formula_field(data_fixture, django_assert_num_queries):

    user = data_fixture.create_user()
    table, fields, rows = data_fixture.build_table(
        columns=[("perf_formula0", "number")], rows=[["0"]], user=user
    )
    fill_table(10000, table)
    num_formulas = 100
    first_field = None
    for i in range(1, num_formulas):
        print(f"Making formula field {i}")
        field = FieldHandler().create_field(
            user=user,
            table=table,
            name=f"perf_formula{i}",
            type_name="formula",
            formula=f"field('perf_formula{i-1}')+1",
        )
        if i == 1:
            first_field = field
    profiler = Profiler()
    profiler.start()
    FieldHandler().update_field(
        user=user,
        table=table,
        field=first_field,
        formula="field('perf_formula0')+2",
    )
    profiler.stop()
    print(profiler.output_text(unicode=True, color=True))


@pytest.mark.django_db
@pytest.mark.slow
# You must add --runslow -s to pytest to run this test, you can do this in intellij by
# editing the run config for this test and adding --runslow -s to additional args.
def test_getting_data_from_a_very_nested_formula_field(data_fixture, api_client):

    user, token = data_fixture.create_user_and_token()
    table, fields, rows = data_fixture.build_table(
        columns=[("perf_formula0", "number")], rows=[["0"]], user=user
    )
    grid = data_fixture.create_grid_view(table=table)
    fill_table(10000, table)
    num_formulas = 100
    for i in range(1, num_formulas):
        print(f"Making formula field {i}")
        FieldHandler().create_field(
            user=user,
            table=table,
            name=f"perf_formula{i}",
            type_name="formula",
            formula=f"field('perf_formula{i-1}')+1",
        )
    url = reverse("api:database:views:grid:list", kwargs={"view_id": grid.id})
    profiler = Profiler()
    profiler.start()
    response = api_client.get(url, **{"HTTP_AUTHORIZATION": f"JWT {token}"})
    profiler.stop()
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["count"] == 10001
    print(profiler.output_text(unicode=True, color=True))


@pytest.mark.django_db
@pytest.mark.slow
# You must add --runslow -s to pytest to run this test, you can do this in intellij by
# editing the run config for this test and adding --runslow -s to additional args.
def test_getting_data_from_normal_table(data_fixture, api_client):

    user, token = data_fixture.create_user_and_token()
    table, fields, rows = data_fixture.build_table(
        columns=[("perf_formula0", "number")], rows=[["0"]], user=user
    )
    grid = data_fixture.create_grid_view(table=table)
    fill_table(10000, table)
    num_fields = 100
    for i in range(1, num_fields):
        print(f"Making field {i}")
        FieldHandler().create_field(
            user=user,
            table=table,
            name=f"normal_field{i}",
            type_name="text",
        )
    url = reverse("api:database:views:grid:list", kwargs={"view_id": grid.id})
    profiler = Profiler()
    profiler.start()
    response = api_client.get(url, **{"HTTP_AUTHORIZATION": f"JWT {token}"})
    profiler.stop()
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["count"] == 10001
    print(profiler.output_text(unicode=True, color=True))
