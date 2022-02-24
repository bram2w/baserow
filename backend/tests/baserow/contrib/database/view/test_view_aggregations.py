import pytest
import random
from decimal import Decimal

from baserow.contrib.database.views.registries import view_aggregation_type_registry
from baserow.contrib.database.views.exceptions import FieldAggregationNotSupported
from baserow.contrib.database.views.handler import ViewHandler
from baserow.contrib.database.fields.exceptions import FieldNotInTable

from baserow.test_utils.helpers import setup_interesting_test_table


@pytest.mark.django_db
def test_view_empty_count_aggregation(data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    text_field = data_fixture.create_text_field(table=table)
    number_field = data_fixture.create_number_field(table=table)
    boolean_field = data_fixture.create_boolean_field(table=table)
    grid_view = data_fixture.create_grid_view(table=table)

    view_handler = ViewHandler()

    model = table.get_model()
    model.objects.create(
        **{
            f"field_{text_field.id}": "Aaa",
            f"field_{number_field.id}": 30,
            f"field_{boolean_field.id}": True,
        }
    )
    model.objects.create(
        **{
            f"field_{text_field.id}": "Aaa",
            f"field_{number_field.id}": 20,
            f"field_{boolean_field.id}": False,
        }
    )
    model.objects.create(
        **{
            f"field_{text_field.id}": "",
            f"field_{number_field.id}": 0,
            f"field_{boolean_field.id}": True,
        }
    )
    model.objects.create(
        **{
            f"field_{text_field.id}": None,
            f"field_{number_field.id}": None,
            f"field_{boolean_field.id}": False,
        }
    )

    result = view_handler.get_field_aggregations(
        grid_view,
        [
            (
                text_field,
                "empty_count",
            ),
            (
                text_field,
                "not_empty_count",
            ),
            (
                boolean_field,
                "empty_count",
            ),
            (
                boolean_field,
                "not_empty_count",
            ),
            (
                number_field,
                "empty_count",
            ),
            (
                number_field,
                "not_empty_count",
            ),
        ],
    )

    assert result[f"field_{text_field.id}__empty_count"] == 2
    assert result[f"field_{text_field.id}__not_empty_count"] == 2

    assert result[f"field_{boolean_field.id}__empty_count"] == 2
    assert result[f"field_{boolean_field.id}__not_empty_count"] == 2

    assert result[f"field_{number_field.id}__empty_count"] == 1
    assert result[f"field_{number_field.id}__not_empty_count"] == 3

    result = view_handler.get_field_aggregations(
        grid_view,
        [
            (
                text_field,
                "empty_count",
            ),
        ],
        with_total=True,
    )

    assert result[f"total"] == 4


@pytest.mark.django_db
def test_view_empty_count_aggregation_for_interesting_table(data_fixture):
    table, _, _, _ = setup_interesting_test_table(data_fixture)
    grid_view = data_fixture.create_grid_view(table=table)

    model = table.get_model()

    view_handler = ViewHandler()

    aggregation_query = []
    for field in model._field_objects.values():

        aggregation_query.append(
            (
                field["field"],
                "empty_count",
            )
        )

        aggregation_query.append(
            (
                field["field"],
                "not_empty_count",
            )
        )

    result = view_handler.get_field_aggregations(
        grid_view, aggregation_query, model=model, with_total=True
    )

    for field in model._field_objects.values():
        field_id = field["field"].id
        assert (
            result[f"field_{field_id}__empty_count"]
            + result[f"field_{field_id}__not_empty_count"]
            == result["total"]
        )


@pytest.mark.django_db
def test_view_unique_count_aggregation_for_interesting_table(data_fixture):
    table, _, _, _ = setup_interesting_test_table(data_fixture)
    grid_view = data_fixture.create_grid_view(table=table)

    model = table.get_model()

    view_handler = ViewHandler()

    aggregation_type = view_aggregation_type_registry.get("unique_count")

    aggregation_query = []
    for field in model._field_objects.values():
        if aggregation_type.field_is_compatible(field["field"]):

            aggregation_query.append(
                (
                    field["field"],
                    "unique_count",
                )
            )

    result = view_handler.get_field_aggregations(
        grid_view, aggregation_query, model=model, with_total=True
    )

    assert len(result.keys()) == 25

    for field in model._field_objects.values():
        if aggregation_type.field_is_compatible(field["field"]):

            field_id = field["field"].id
            field_type = field["type"].type

            if field_type in ["url", "email", "rating", "phone_number"]:
                assert result[f"field_{field_id}__unique_count"] == 2
            else:
                assert result[f"field_{field_id}__unique_count"] == 1


@pytest.mark.django_db
def test_view_number_aggregation(data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    number_field = data_fixture.create_number_field(table=table)
    grid_view = data_fixture.create_grid_view(table=table)

    view_handler = ViewHandler()

    model = table.get_model()

    random.seed(12345)

    for i in range(30):
        model.objects.create(
            **{
                f"field_{number_field.id}": random.randint(0, 100),
            }
        )

    model.objects.create(
        **{
            f"field_{number_field.id}": None,
        }
    )

    result = view_handler.get_field_aggregations(
        grid_view,
        [
            (
                number_field,
                "min",
            ),
            (
                number_field,
                "max",
            ),
            (
                number_field,
                "sum",
            ),
            (
                number_field,
                "average",
            ),
            (
                number_field,
                "median",
            ),
            (
                number_field,
                "std_dev",
            ),
            (
                number_field,
                "variance",
            ),
            (
                number_field,
                "decile",
            ),
        ],
    )

    assert result[f"field_{number_field.id}__min"] == 1
    assert result[f"field_{number_field.id}__max"] == 94
    assert result[f"field_{number_field.id}__sum"] == 1546
    assert round(result[f"field_{number_field.id}__median"], 2) == Decimal("52.5")
    assert round(result[f"field_{number_field.id}__average"], 2) == Decimal("51.53")
    assert round(result[f"field_{number_field.id}__std_dev"], 2) == Decimal("26.73")
    assert round(result[f"field_{number_field.id}__variance"], 2) == Decimal("714.72")
    assert result[f"field_{number_field.id}__decile"] == [
        19.5,
        22.8,
        33.7,
        46.2,
        52.5,
        58.6,
        70.3,
        74.8,
        93.0,
    ]


@pytest.mark.django_db
def test_view_aggregation_errors(data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    text_field = data_fixture.create_text_field(table=table)
    form_view = data_fixture.create_form_view(table=table)

    table2 = data_fixture.create_database_table(user=user)
    data_fixture.create_text_field(table=table2)
    grid_view = data_fixture.create_grid_view(table=table2)

    view_handler = ViewHandler()

    with pytest.raises(FieldAggregationNotSupported):
        view_handler.get_field_aggregations(
            form_view,
            [
                (
                    text_field,
                    "empty_count",
                ),
            ],
        )

    with pytest.raises(FieldNotInTable):
        view_handler.get_field_aggregations(
            grid_view,
            [
                (
                    text_field,
                    "empty_count",
                ),
            ],
        )
