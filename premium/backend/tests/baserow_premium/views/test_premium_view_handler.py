import pytest

from baserow.contrib.database.views.models import View, ViewDecoration
from baserow_premium.views.handler import get_rows_grouped_by_single_select_field
from baserow.contrib.database.fields.handler import FieldHandler


@pytest.mark.django_db
def test_get_rows_grouped_by_single_select_field(
    premium_data_fixture, django_assert_num_queries
):
    table = premium_data_fixture.create_database_table()
    view = View()
    view.table = table
    text_field = premium_data_fixture.create_text_field(table=table, primary=True)
    single_select_field = premium_data_fixture.create_single_select_field(table=table)
    option_a = premium_data_fixture.create_select_option(
        field=single_select_field, value="A", color="blue"
    )
    option_b = premium_data_fixture.create_select_option(
        field=single_select_field, value="B", color="red"
    )

    model = table.get_model()
    row_none1 = model.objects.create(
        **{
            f"field_{text_field.id}": "Row None 1",
            f"field_{single_select_field.id}_id": None,
        }
    )
    row_none2 = model.objects.create(
        **{
            f"field_{text_field.id}": "Row None 2",
            f"field_{single_select_field.id}_id": None,
        }
    )
    row_a1 = model.objects.create(
        **{
            f"field_{text_field.id}": "Row A1",
            f"field_{single_select_field.id}_id": option_a.id,
        }
    )
    row_a2 = model.objects.create(
        **{
            f"field_{text_field.id}": "Row A2",
            f"field_{single_select_field.id}_id": option_a.id,
        }
    )
    row_b1 = model.objects.create(
        **{
            f"field_{text_field.id}": "Row B1",
            f"field_{single_select_field.id}_id": option_b.id,
        }
    )
    row_b2 = model.objects.create(
        **{
            f"field_{text_field.id}": "Row B2",
            f"field_{single_select_field.id}_id": option_b.id,
        }
    )

    # The amount of queries including
    with django_assert_num_queries(4):
        rows = get_rows_grouped_by_single_select_field(
            view, single_select_field, model=model
        )

    assert len(rows) == 3
    assert rows["null"]["count"] == 2
    assert len(rows["null"]["results"]) == 2
    assert rows["null"]["results"][0].id == row_none1.id
    assert rows["null"]["results"][1].id == row_none2.id

    assert rows[str(option_a.id)]["count"] == 2
    assert len(rows[str(option_a.id)]["results"]) == 2
    assert rows[str(option_a.id)]["results"][0].id == row_a1.id
    assert rows[str(option_a.id)]["results"][1].id == row_a2.id

    assert rows[str(option_b.id)]["count"] == 2
    assert len(rows[str(option_b.id)]["results"]) == 2
    assert rows[str(option_b.id)]["results"][0].id == row_b1.id
    assert rows[str(option_b.id)]["results"][1].id == row_b2.id

    rows = get_rows_grouped_by_single_select_field(
        view, single_select_field, default_limit=1
    )

    assert len(rows) == 3
    assert rows["null"]["count"] == 2
    assert len(rows["null"]["results"]) == 1
    assert rows["null"]["results"][0].id == row_none1.id

    assert rows[str(option_a.id)]["count"] == 2
    assert len(rows[str(option_a.id)]["results"]) == 1
    assert rows[str(option_a.id)]["results"][0].id == row_a1.id

    assert rows[str(option_b.id)]["count"] == 2
    assert len(rows[str(option_b.id)]["results"]) == 1
    assert rows[str(option_b.id)]["results"][0].id == row_b1.id

    rows = get_rows_grouped_by_single_select_field(
        view, single_select_field, default_limit=1, default_offset=1
    )

    assert len(rows) == 3
    assert rows["null"]["count"] == 2
    assert len(rows["null"]["results"]) == 1
    assert rows["null"]["results"][0].id == row_none2.id

    assert rows[str(option_a.id)]["count"] == 2
    assert len(rows[str(option_a.id)]["results"]) == 1
    assert rows[str(option_a.id)]["results"][0].id == row_a2.id

    assert rows[str(option_b.id)]["count"] == 2
    assert len(rows[str(option_b.id)]["results"]) == 1
    assert rows[str(option_b.id)]["results"][0].id == row_b2.id

    rows = get_rows_grouped_by_single_select_field(
        view,
        single_select_field,
        option_settings={"null": {"limit": 1, "offset": 1}},
    )

    assert len(rows) == 1
    assert rows["null"]["count"] == 2
    assert len(rows["null"]["results"]) == 1
    assert rows["null"]["results"][0].id == row_none2.id

    rows = get_rows_grouped_by_single_select_field(
        view,
        single_select_field,
        option_settings={
            str(option_a.id): {"limit": 1, "offset": 0},
            str(option_b.id): {"limit": 1, "offset": 1},
        },
    )

    assert len(rows) == 2

    assert rows[str(option_a.id)]["count"] == 2
    assert len(rows[str(option_a.id)]["results"]) == 1
    assert rows[str(option_a.id)]["results"][0].id == row_a1.id

    assert rows[str(option_b.id)]["count"] == 2
    assert len(rows[str(option_b.id)]["results"]) == 1
    assert rows[str(option_b.id)]["results"][0].id == row_b2.id

    rows = get_rows_grouped_by_single_select_field(
        view,
        single_select_field,
        option_settings={
            str(option_a.id): {"limit": 10, "offset": 10},
        },
    )

    assert len(rows) == 1
    assert rows[str(option_a.id)]["count"] == 2
    assert len(rows[str(option_a.id)]["results"]) == 0


@pytest.mark.django_db
def test_get_rows_grouped_by_single_select_field_not_existing_options_are_null(
    premium_data_fixture,
):
    table = premium_data_fixture.create_database_table()
    view = View()
    view.table = table
    text_field = premium_data_fixture.create_text_field(table=table, primary=True)
    single_select_field = premium_data_fixture.create_single_select_field(table=table)
    option_a = premium_data_fixture.create_select_option(
        field=single_select_field, value="A", color="blue"
    )
    option_b = premium_data_fixture.create_select_option(
        field=single_select_field, value="B", color="red"
    )

    model = table.get_model()
    row_1 = model.objects.create(
        **{
            f"field_{text_field.id}": "Row 1",
            f"field_{single_select_field.id}_id": None,
        }
    )
    row_2 = model.objects.create(
        **{
            f"field_{text_field.id}": "Row 2",
            f"field_{single_select_field.id}_id": option_a.id,
        }
    )
    row_3 = model.objects.create(
        **{
            f"field_{text_field.id}": "Row 3",
            f"field_{single_select_field.id}_id": option_b.id,
        }
    )

    option_b.delete()
    rows = get_rows_grouped_by_single_select_field(
        view, single_select_field, model=model
    )

    assert len(rows) == 2
    assert rows["null"]["count"] == 2
    assert len(rows["null"]["results"]) == 2
    assert rows["null"]["results"][0].id == row_1.id
    assert rows["null"]["results"][1].id == row_3.id
    assert rows[str(option_a.id)]["count"] == 1
    assert len(rows[str(option_a.id)]["results"]) == 1
    assert rows[str(option_a.id)]["results"][0].id == row_2.id

    option_a.delete()
    rows = get_rows_grouped_by_single_select_field(
        view, single_select_field, model=model
    )

    assert len(rows) == 1
    assert rows["null"]["count"] == 3
    assert len(rows["null"]["results"]) == 3
    assert rows["null"]["results"][0].id == row_1.id
    assert rows["null"]["results"][1].id == row_2.id
    assert rows["null"]["results"][2].id == row_3.id


@pytest.mark.django_db
def test_get_rows_grouped_by_single_select_field_with_empty_table(
    premium_data_fixture,
):
    table = premium_data_fixture.create_database_table()
    view = View()
    view.table = table
    single_select_field = premium_data_fixture.create_single_select_field(table=table)
    rows = get_rows_grouped_by_single_select_field(view, single_select_field)
    assert len(rows) == 1
    assert rows["null"]["count"] == 0
    assert len(rows["null"]["results"]) == 0


@pytest.mark.django_db
def test_field_type_changed_w_decoration(data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    text_field = data_fixture.create_text_field(table=table)
    option_field = data_fixture.create_single_select_field(
        table=table, name="option_field", order=1
    )
    option_a = data_fixture.create_select_option(
        field=option_field, value="A", color="blue"
    )

    grid_view = data_fixture.create_grid_view(table=table)

    select_view_decoration = data_fixture.create_view_decoration(
        view=grid_view,
        value_provider_type="single_select_color",
        value_provider_conf={"field_id": option_field.id},
        order=1,
    )

    condition_view_decoration = data_fixture.create_view_decoration(
        view=grid_view,
        value_provider_type="conditional_color",
        value_provider_conf={
            "colors": [
                {"filters": [{"field": text_field.id, "type": "equal"}]},
                {"filters": [{"field": option_field.id, "type": "equal"}]},
                {
                    "filters": [
                        {"field": option_field.id, "type": "single_select_equal"}
                    ]
                },
                {"filters": []},
            ]
        },
        order=2,
    )

    field_handler = FieldHandler()

    decorations = list(ViewDecoration.objects.all())
    assert len(decorations) == 2
    assert (
        decorations[0].value_provider_conf == select_view_decoration.value_provider_conf
    )
    assert (
        decorations[1].value_provider_conf
        == condition_view_decoration.value_provider_conf
    )

    field_handler.update_field(
        user=user, field=option_field, new_type_name="single_select"
    )

    decorations = list(ViewDecoration.objects.all())
    assert (
        decorations[0].value_provider_conf == select_view_decoration.value_provider_conf
    )
    assert (
        decorations[1].value_provider_conf
        == condition_view_decoration.value_provider_conf
    )

    field_handler.update_field(user=user, field=option_field, new_type_name="text")

    decorations = list(ViewDecoration.objects.all())
    assert decorations[0].value_provider_conf == {"field_id": None}
    assert decorations[1].value_provider_conf == {
        "colors": [
            {"filters": [{"type": "equal", "field": text_field.id}]},
            {"filters": [{"type": "equal", "field": option_field.id}]},
            {"filters": []},
            {"filters": []},
        ]
    }


@pytest.mark.django_db
def test_field_deleted_w_decoration(data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    text_field = data_fixture.create_text_field(table=table)
    option_field = data_fixture.create_single_select_field(
        table=table, name="option_field", order=1
    )
    option_a = data_fixture.create_select_option(
        field=option_field, value="A", color="blue"
    )

    grid_view = data_fixture.create_grid_view(table=table)

    select_view_decoration = data_fixture.create_view_decoration(
        view=grid_view,
        value_provider_type="single_select_color",
        value_provider_conf={"field_id": option_field.id},
        order=1,
    )

    condition_view_decoration = data_fixture.create_view_decoration(
        view=grid_view,
        value_provider_type="conditional_color",
        value_provider_conf={
            "colors": [
                {"filters": [{"field": text_field.id, "type": "equal"}]},
                {"filters": [{"field": option_field.id, "type": "equal"}]},
                {
                    "filters": [
                        {"field": option_field.id, "type": "single_select_equal"}
                    ]
                },
                {"filters": []},
            ]
        },
        order=2,
    )

    field_handler = FieldHandler()

    field_handler.delete_field(user=user, field=option_field)

    decorations = list(ViewDecoration.objects.all())
    assert decorations[0].value_provider_conf == {"field_id": None}
    assert decorations[1].value_provider_conf == {
        "colors": [
            {"filters": [{"type": "equal", "field": text_field.id}]},
            {"filters": []},
            {"filters": []},
            {"filters": []},
        ]
    }

    field_handler.delete_field(user=user, field=text_field)

    decorations = list(ViewDecoration.objects.all())
    assert decorations[0].value_provider_conf == {"field_id": None}
    assert decorations[1].value_provider_conf == {
        "colors": [
            {"filters": []},
            {"filters": []},
            {"filters": []},
            {"filters": []},
        ]
    }
