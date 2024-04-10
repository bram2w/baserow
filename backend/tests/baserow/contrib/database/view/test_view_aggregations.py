import random
from decimal import Decimal

import pytest

from baserow.contrib.database.fields.exceptions import FieldNotInTable
from baserow.contrib.database.fields.handler import FieldHandler
from baserow.contrib.database.views.exceptions import FieldAggregationNotSupported
from baserow.contrib.database.views.handler import ViewHandler
from baserow.contrib.database.views.registries import view_aggregation_type_registry
from baserow.core.trash.handler import TrashHandler
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
        user,
        grid_view,
        [
            (
                text_field,
                "empty_count",
            ),
            (
                boolean_field,
                "empty_count",
            ),
            (
                number_field,
                "empty_count",
            ),
        ],
    )

    assert result[f"field_{text_field.id}"] == 2
    assert result[f"field_{boolean_field.id}"] == 2
    assert result[f"field_{number_field.id}"] == 1

    result = view_handler.get_field_aggregations(
        user,
        grid_view,
        [
            (
                text_field,
                "not_empty_count",
            ),
            (
                boolean_field,
                "not_empty_count",
            ),
            (
                number_field,
                "not_empty_count",
            ),
        ],
    )
    assert result[f"field_{text_field.id}"] == 2
    assert result[f"field_{boolean_field.id}"] == 2
    assert result[f"field_{number_field.id}"] == 3

    result = view_handler.get_field_aggregations(
        user,
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
    user = data_fixture.create_user()
    table, _, _, _, context = setup_interesting_test_table(data_fixture, user=user)
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

    result_empty = view_handler.get_field_aggregations(
        user, grid_view, aggregation_query, model=model, with_total=True
    )

    aggregation_query = []
    for field in model._field_objects.values():
        aggregation_query.append(
            (
                field["field"],
                "not_empty_count",
            )
        )

    result_not_empty = view_handler.get_field_aggregations(
        user, grid_view, aggregation_query, model=model
    )

    for field in model._field_objects.values():
        assert (
            result_empty[field["field"].db_column]
            + result_not_empty[field["field"].db_column]
            == result_empty["total"]
        )


@pytest.mark.django_db
def test_view_unique_count_aggregation_for_interesting_table(data_fixture):
    user = data_fixture.create_user()
    table, _, _, _, context = setup_interesting_test_table(data_fixture, user=user)
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
        user, grid_view, aggregation_query, model=model, with_total=True
    )

    assert (
        len(result.keys()) == len(aggregation_query) + 1
    ), f"{result} vs {aggregation_query}"

    for field_obj in model._field_objects.values():
        field = field_obj["field"]
        if aggregation_type.field_is_compatible(field):
            field_id = field.id
            field_type = field_obj["type"].type

            if (
                field_type
                in [
                    "url",
                    "email",
                    "rating",
                    "phone_number",
                    "count",
                    "rollup",
                ]
                or field_type == "formula"
                and field.formula_type == "char"
            ):
                assert result[f"field_{field_id}"] == 2
            else:
                assert result[f"field_{field_id}"] == 1


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
                number_field.db_column: random.randint(0, 100),
            }
        )

    model.objects.create(
        **{
            number_field.db_column: None,
        }
    )

    result = view_handler.get_field_aggregations(
        user,
        grid_view,
        [
            (
                number_field,
                "min",
            ),
        ],
    )
    assert result[number_field.db_column] == 1

    result = view_handler.get_field_aggregations(
        user,
        grid_view,
        [
            (
                number_field,
                "max",
            ),
        ],
    )
    assert result[number_field.db_column] == 94

    result = view_handler.get_field_aggregations(
        user,
        grid_view,
        [
            (
                number_field,
                "sum",
            ),
        ],
    )

    assert result[number_field.db_column] == 1546

    result = view_handler.get_field_aggregations(
        user,
        grid_view,
        [
            (
                number_field,
                "average",
            ),
        ],
    )
    assert round(result[number_field.db_column], 2) == Decimal("51.53")

    result = view_handler.get_field_aggregations(
        user,
        grid_view,
        [
            (
                number_field,
                "median",
            ),
        ],
    )
    assert round(result[number_field.db_column], 2) == Decimal("52.5")

    result = view_handler.get_field_aggregations(
        user,
        grid_view,
        [
            (
                number_field,
                "std_dev",
            ),
        ],
    )
    assert round(result[number_field.db_column], 2) == Decimal("26.73")

    result = view_handler.get_field_aggregations(
        user,
        grid_view,
        [
            (
                number_field,
                "variance",
            ),
        ],
    )
    assert round(result[number_field.db_column], 2) == Decimal("714.72")

    result = view_handler.get_field_aggregations(
        user,
        grid_view,
        [
            (
                number_field,
                "decile",
            ),
        ],
    )
    assert list(map(lambda x: round(x, 1), result[number_field.db_column])) == [
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
            user,
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
            user,
            grid_view,
            [
                (
                    text_field,
                    "empty_count",
                ),
            ],
        )


@pytest.mark.django_db
def test_aggregation_is_updated_when_view_is_trashed(data_fixture):
    """
    Test that aggregation is updated when view is trashed

    The following scenario is tested:
    - Create two views
    - Creat a field in both views
    - Create and aggregation in both views
    - Trash that view
    - Change the field type to a different type that is
      incompatible with the aggregation
    - Restore the view
    - Check that the aggregation is updated
    """

    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    grid_view_one = data_fixture.create_grid_view(table=table)
    grid_view_two = data_fixture.create_grid_view(table=table)
    field = data_fixture.create_number_field(user=user, table=table)
    application = table.database

    view_handler = ViewHandler()

    model = table.get_model()

    model.objects.create(**{field.db_column: 1})
    model.objects.create(**{field.db_column: 2})

    view_handler.update_field_options(
        view=grid_view_one,
        field_options={
            field.id: {
                "aggregation_type": "sum",
                "aggregation_raw_type": "sum",
            }
        },
    )

    view_handler.update_field_options(
        view=grid_view_two,
        field_options={
            field.id: {
                "aggregation_type": "sum",
                "aggregation_raw_type": "sum",
            }
        },
    )

    # Verify both views have an aggregation
    aggregations_view_one = view_handler.get_view_field_aggregations(
        user, grid_view_one
    )
    aggregations_view_two = view_handler.get_view_field_aggregations(
        user, grid_view_two
    )

    assert field.db_column in aggregations_view_one
    assert field.db_column in aggregations_view_two

    # Trash the view and verify that the aggregation is not retrievable anymore
    TrashHandler().trash(
        user, application.workspace, application, trash_item=grid_view_one
    )
    aggregations = view_handler.get_view_field_aggregations(user, grid_view_one)

    assert field.db_column not in aggregations

    # Update the field and verify that the aggregation is removed from the
    # not trashed view
    FieldHandler().update_field(user, field, new_type_name="text")
    aggregations_not_trashed_view = view_handler.get_view_field_aggregations(
        user, grid_view_two
    )
    assert field.db_column not in aggregations_not_trashed_view

    # Restore the view and verify that the aggregation
    # is also removed from the restored view
    TrashHandler().restore_item(user, "view", grid_view_one.id)
    aggregations_restored_view = view_handler.get_view_field_aggregations(
        user, grid_view_one
    )
    assert field.db_column not in aggregations_restored_view
