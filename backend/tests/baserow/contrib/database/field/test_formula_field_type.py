import pytest

from baserow.contrib.database.fields.handler import FieldHandler
from baserow.contrib.database.fields.registries import field_type_registry
from baserow.contrib.database.formula.types.formula_type import (
    BaserowFormulaInvalidType,
)
from baserow.contrib.database.rows.handler import RowHandler
from baserow.contrib.database.views.handler import ViewHandler


@pytest.mark.django_db
def test_creating_a_model_with_formula_field_immediately_populates_it(data_fixture):
    table = data_fixture.create_database_table()
    formula_field = data_fixture.create_formula_field(
        table=table, formula="'test'", formula_type="text"
    )
    formula_field_name = f"field_{formula_field.id}"
    model = table.get_model()
    row = model.objects.create()

    assert getattr(row, formula_field_name) == "test"


@pytest.mark.django_db
def test_adding_a_formula_field_to_an_existing_table_populates_it_for_all_rows(
    data_fixture,
):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    before_model = table.get_model()
    existing_row = before_model.objects.create()
    formula_field = FieldHandler().create_field(
        user, table, "formula", name="formula", formula="'test'"
    )
    formula_field_name = f"field_{formula_field.id}"
    model = table.get_model()
    row = model.objects.create()

    assert getattr(row, formula_field_name) == "test"
    assert getattr(model.objects.get(id=existing_row.id), formula_field_name) == "test"


@pytest.mark.django_db
def test_cant_change_the_value_of_a_formula_field_directly(data_fixture):
    table = data_fixture.create_database_table()
    data_fixture.create_formula_field(
        name="formula", table=table, formula="'test'", formula_type="text"
    )
    data_fixture.create_text_field(name="text", table=table)
    model = table.get_model(attribute_names=True)

    row = model.objects.create(formula="not test")
    assert row.formula == "test"

    row.text = "update other field"
    row.save()

    row.formula = "not test"
    row.save()
    row.refresh_from_db()
    assert row.formula == "test"


@pytest.mark.django_db
def test_get_set_export_serialized_value_formula_field(data_fixture):
    table = data_fixture.create_database_table()
    formula_field = data_fixture.create_formula_field(
        table=table, formula="'test'", formula_type="text"
    )
    formula_field_name = f"field_{formula_field.id}"
    formula_field_type = field_type_registry.get_by_model(formula_field)

    model = table.get_model()
    row_1 = model.objects.create()
    row_2 = model.objects.create()

    old_row_1_value = getattr(row_1, formula_field_name)
    old_row_2_value = getattr(row_2, formula_field_name)

    assert old_row_1_value == "test"
    assert old_row_2_value == "test"

    formula_field_type.set_import_serialized_value(
        row_1,
        formula_field_name,
        formula_field_type.get_export_serialized_value(
            row_1, formula_field_name, {}, None, None
        ),
        {},
        None,
        None,
    )
    formula_field_type.set_import_serialized_value(
        row_2,
        formula_field_name,
        formula_field_type.get_export_serialized_value(
            row_2, formula_field_name, {}, None, None
        ),
        {},
        None,
        None,
    )

    row_1.save()
    row_2.save()

    row_1.refresh_from_db()
    row_2.refresh_from_db()

    assert old_row_1_value == getattr(row_1, formula_field_name)
    assert old_row_2_value == getattr(row_2, formula_field_name)


@pytest.mark.django_db
def test_changing_type_of_other_field_still_results_in_working_filter(data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    grid_view = data_fixture.create_grid_view(user, table=table)
    first_formula_field = data_fixture.create_formula_field(
        table=table, formula="'test'", formula_type="text", name="source"
    )
    formula_field_referencing_first_field = data_fixture.create_formula_field(
        table=table, formula="field('source')", formula_type="text"
    )

    data_fixture.create_view_filter(
        user=user,
        view=grid_view,
        field=formula_field_referencing_first_field,
        type="equal",
        value="t",
    )

    # Change the first formula field to be a boolean field, meaning that the view
    # filter on the referencing formula field is now and invalid and should be deleted
    FieldHandler().update_field(user, first_formula_field, formula="1")

    queryset = ViewHandler().get_queryset(grid_view)
    assert not queryset.exists()
    assert queryset.count() == 0


@pytest.mark.django_db
def test_can_use_complex_date_filters_on_formula_field(data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    grid_view = data_fixture.create_grid_view(user, table=table)
    data_fixture.create_date_field(user=user, table=table, name="date_field")
    formula_field = data_fixture.create_formula_field(
        table=table, formula="field('date_field')", formula_type="date", name="formula"
    )

    data_fixture.create_view_filter(
        user=user,
        view=grid_view,
        field=formula_field,
        type="date_equals_today",
        value="Europe/London",
    )

    queryset = ViewHandler().get_queryset(grid_view)
    assert not queryset.exists()
    assert queryset.count() == 0


@pytest.mark.django_db
def test_can_use_complex_contains_filters_on_formula_field(data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    grid_view = data_fixture.create_grid_view(user, table=table)
    data_fixture.create_date_field(
        user=user, table=table, name="date_field", date_format="US"
    )
    formula_field = data_fixture.create_formula_field(
        table=table,
        formula="field('date_field')",
        formula_type="date",
        name="formula",
        date_format="US",
        date_time_format="24",
    )

    data_fixture.create_view_filter(
        user=user,
        view=grid_view,
        field=formula_field,
        type="contains",
        value="23",
    )

    queryset = ViewHandler().get_queryset(grid_view)
    assert not queryset.exists()
    assert queryset.count() == 0


@pytest.mark.django_db
def test_can_change_formula_type_breaking_other_fields(data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    handler = FieldHandler()
    first_formula_field = handler.create_field(
        user=user, table=table, name="1", type_name="formula", formula="1+1"
    )
    second_formula_field = handler.create_field(
        user=user, table=table, type_name="formula", name="2", formula="field('1')+1"
    )
    handler.update_field(
        user=user, field=first_formula_field, new_type_name="formula", formula="'a'"
    )
    second_formula_field.refresh_from_db()
    assert second_formula_field.formula_type == BaserowFormulaInvalidType.type
    assert "argument number 2" in second_formula_field.error


@pytest.mark.django_db
def test_can_still_insert_rows_with_an_invalid_but_previously_date_formula_field(
    data_fixture,
):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    handler = FieldHandler()
    date_field = handler.create_field(
        user=user, table=table, name="1", type_name="date"
    )
    formula_field = handler.create_field(
        user=user, table=table, type_name="formula", name="2", formula="field('1')"
    )
    handler.update_field(user=user, field=date_field, new_type_name="single_select")

    row = RowHandler().create_row(user=user, table=table)
    assert getattr(row, f"field_{formula_field.id}") is None


@pytest.mark.django_db
def test_formula_with_row_id_is_populated_after_creating_row(
    data_fixture,
):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    handler = FieldHandler()
    formula_field = handler.create_field(
        user=user, table=table, type_name="formula", name="2", formula="row_id()"
    )

    row = RowHandler().create_row(user=user, table=table)
    assert getattr(row, f"field_{formula_field.id}") == row.id


@pytest.mark.django_db
def test_can_rename_field_preserving_whitespace(
    data_fixture,
):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    handler = FieldHandler()
    test_field = handler.create_field(
        user=user, table=table, type_name="text", name="a"
    )
    formula_field = handler.create_field(
        user=user, table=table, type_name="formula", name="2", formula=" field('a') \n"
    )

    assert formula_field.formula == f" field('a') \n"

    handler.update_field(user=user, field=test_field, name="b")

    formula_field.refresh_from_db()

    assert formula_field.formula == f" field('b') \n"
