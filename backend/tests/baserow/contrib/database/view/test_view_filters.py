import pytest
from datetime import date
from pytz import timezone

from django.utils.timezone import make_aware, datetime

from baserow.contrib.database.views.registries import view_filter_type_registry
from baserow.contrib.database.views.handler import ViewHandler
from baserow.contrib.database.fields.handler import FieldHandler


@pytest.mark.django_db
def test_equal_filter_type(data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    grid_view = data_fixture.create_grid_view(table=table)
    text_field = data_fixture.create_text_field(table=table)
    long_text_field = data_fixture.create_long_text_field(table=table)
    integer_field = data_fixture.create_number_field(table=table)
    decimal_field = data_fixture.create_number_field(
        table=table, number_type="DECIMAL", number_decimal_places=2
    )
    boolean_field = data_fixture.create_boolean_field(table=table)

    handler = ViewHandler()
    model = table.get_model()

    row = model.objects.create(
        **{
            f"field_{text_field.id}": "Test",
            f"field_{long_text_field.id}": "Long",
            f"field_{integer_field.id}": 10,
            f"field_{decimal_field.id}": 20.20,
            f"field_{boolean_field.id}": True,
        }
    )
    row_2 = model.objects.create(
        **{
            f"field_{text_field.id}": "",
            f"field_{long_text_field.id}": "",
            f"field_{integer_field.id}": None,
            f"field_{decimal_field.id}": None,
            f"field_{boolean_field.id}": False,
        }
    )
    row_3 = model.objects.create(
        **{
            f"field_{text_field.id}": "NOT",
            f"field_{long_text_field.id}": "NOT2",
            f"field_{integer_field.id}": 99,
            f"field_{decimal_field.id}": 99.99,
            f"field_{boolean_field.id}": False,
        }
    )

    filter = data_fixture.create_view_filter(
        view=grid_view, field=text_field, type="equal", value="Test"
    )
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 1
    assert row.id in ids

    filter.field = long_text_field
    filter.value = "Long"
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 1
    assert row.id in ids

    filter.field = integer_field
    filter.value = "10"
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 1
    assert row.id in ids

    # Because the value 'test' cannot be accepted the filter is not applied so it will
    # return all rows.
    filter.field = integer_field
    filter.value = "test"
    filter.save()
    assert handler.apply_filters(grid_view, model.objects.all()).count() == 3

    filter.field = decimal_field
    filter.value = "20.20"
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 1
    assert row.id in ids

    filter.field = boolean_field
    filter.value = "1"
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 1
    assert row.id in ids

    filter.field = boolean_field
    filter.value = "0"
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 2
    assert row_2.id in ids
    assert row_3.id in ids

    filter.field = text_field
    filter.value = ""
    filter.save()
    assert handler.apply_filters(grid_view, model.objects.all()).count() == 3

    filter.field = long_text_field
    filter.value = ""
    filter.save()
    assert handler.apply_filters(grid_view, model.objects.all()).count() == 3

    filter.field = integer_field
    filter.value = ""
    filter.save()
    assert handler.apply_filters(grid_view, model.objects.all()).count() == 3

    filter.field = decimal_field
    filter.value = ""
    filter.save()
    assert handler.apply_filters(grid_view, model.objects.all()).count() == 3

    filter.field = boolean_field
    filter.value = ""
    filter.save()
    assert handler.apply_filters(grid_view, model.objects.all()).count() == 3


@pytest.mark.django_db
def test_not_equal_filter_type(data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    grid_view = data_fixture.create_grid_view(table=table)
    text_field = data_fixture.create_text_field(table=table)
    long_text_field = data_fixture.create_long_text_field(table=table)
    integer_field = data_fixture.create_number_field(table=table)
    decimal_field = data_fixture.create_number_field(
        table=table, number_type="DECIMAL", number_decimal_places=2
    )
    boolean_field = data_fixture.create_boolean_field(table=table)

    handler = ViewHandler()
    model = table.get_model()

    row = model.objects.create(
        **{
            f"field_{text_field.id}": "Test",
            f"field_{long_text_field.id}": "Long",
            f"field_{integer_field.id}": 10,
            f"field_{decimal_field.id}": 20.20,
            f"field_{boolean_field.id}": True,
        }
    )
    row_2 = model.objects.create(
        **{
            f"field_{text_field.id}": "",
            f"field_{long_text_field.id}": "",
            f"field_{integer_field.id}": None,
            f"field_{decimal_field.id}": None,
            f"field_{boolean_field.id}": False,
        }
    )
    row_3 = model.objects.create(
        **{
            f"field_{text_field.id}": "NOT",
            f"field_{long_text_field.id}": "NOT2",
            f"field_{integer_field.id}": 99,
            f"field_{decimal_field.id}": 99.99,
            f"field_{boolean_field.id}": False,
        }
    )

    filter = data_fixture.create_view_filter(
        view=grid_view, field=text_field, type="not_equal", value="Test"
    )
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 2
    assert row_2.id in ids
    assert row_3.id in ids

    filter.field = long_text_field
    filter.value = "Long"
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 2
    assert row_2.id in ids
    assert row_3.id in ids

    filter.field = integer_field
    filter.value = "10"
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 2
    assert row_2.id in ids
    assert row_3.id in ids

    # Because the value 'test' cannot be accepted the filter is not applied so it will
    # return all rows.
    filter.field = integer_field
    filter.value = "test"
    filter.save()
    assert handler.apply_filters(grid_view, model.objects.all()).count() == 3

    filter.field = decimal_field
    filter.value = "20.20"
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 2
    assert row_2.id in ids
    assert row_3.id in ids

    filter.field = boolean_field
    filter.value = "1"
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 2
    assert row_2.id in ids
    assert row_3.id in ids

    filter.field = boolean_field
    filter.value = "0"
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 1
    assert row.id in ids

    filter.field = text_field
    filter.value = ""
    filter.save()
    assert handler.apply_filters(grid_view, model.objects.all()).count() == 3

    filter.field = long_text_field
    filter.value = ""
    filter.save()
    assert handler.apply_filters(grid_view, model.objects.all()).count() == 3

    filter.field = integer_field
    filter.value = ""
    filter.save()
    assert handler.apply_filters(grid_view, model.objects.all()).count() == 3

    filter.field = decimal_field
    filter.value = ""
    filter.save()
    assert handler.apply_filters(grid_view, model.objects.all()).count() == 3

    filter.field = boolean_field
    filter.value = ""
    filter.save()
    assert handler.apply_filters(grid_view, model.objects.all()).count() == 3


@pytest.mark.django_db
def test_contains_filter_type(data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    grid_view = data_fixture.create_grid_view(table=table)
    text_field = data_fixture.create_text_field(table=table)
    long_text_field = data_fixture.create_long_text_field(table=table)
    date_field = data_fixture.create_date_field(
        table=table, date_include_time=True, date_format="ISO"
    )
    number_field = data_fixture.create_number_field(
        table=table,
        number_type="DECIMAL",
        number_negative=True,
        number_decimal_places=2,
    )
    single_select_field = data_fixture.create_single_select_field(table=table)
    option_a = data_fixture.create_select_option(
        field=single_select_field, value="AC", color="blue"
    )
    option_b = data_fixture.create_select_option(
        field=single_select_field, value="BC", color="red"
    )

    handler = ViewHandler()
    model = table.get_model()

    row = model.objects.create(
        **{
            f"field_{text_field.id}": "My name is John Doe.",
            f"field_{long_text_field.id}": "Long text that is not empty.",
            f"field_{date_field.id}": "2020-02-01 01:23",
            f"field_{number_field.id}": "98989898",
            f"field_{single_select_field.id}": option_a,
        }
    )
    model.objects.create(
        **{
            f"field_{text_field.id}": "",
            f"field_{long_text_field.id}": "",
            f"field_{date_field.id}": None,
            f"field_{number_field.id}": None,
            f"field_{single_select_field.id}": None,
        }
    )
    row_3 = model.objects.create(
        **{
            f"field_{text_field.id}": "This is a test field.",
            f"field_{long_text_field.id}": "This text is a bit longer, but it also "
            "contains.\n A multiline approach.",
            f"field_{date_field.id}": "0001-01-01 00:12",
            f"field_{number_field.id}": "10000",
            f"field_{single_select_field.id}": option_b,
        }
    )

    filter = data_fixture.create_view_filter(
        view=grid_view, field=text_field, type="contains", value="john"
    )
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 1
    assert row.id in ids

    filter.value = "DOE"
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 1
    assert row.id in ids

    filter.value = "test"
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 1
    assert row_3.id in ids

    filter.value = " is "
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 2
    assert row.id in ids
    assert row_3.id in ids

    filter.value = ""
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 3

    filter.value = "random"
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 0

    filter.field = long_text_field
    filter.value = "multiLINE"
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 1
    assert row_3.id in ids

    filter.field = date_field
    filter.value = "2020-02-01"
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 1
    assert row.id in ids

    filter.field = date_field
    filter.value = "01/02/2020"
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 0

    filter.field = date_field
    filter.value = ""
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 3

    filter.field = number_field
    filter.value = "98"
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 1
    assert row.id in ids

    filter.field = number_field
    filter.value = "0" + str(row.id)
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 0

    filter.field = number_field
    filter.value = ""
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 3

    filter.field = date_field
    filter.value = "00:12"
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 1
    assert row_3.id in ids

    filter.field = single_select_field
    filter.value = "A"
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 1
    assert row.id in ids

    filter.field = single_select_field
    filter.value = ""
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 3

    filter.field = single_select_field
    filter.value = "C"
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 2
    assert row.id in ids
    assert row_3.id in ids


@pytest.mark.django_db
def test_contains_not_filter_type(data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    grid_view = data_fixture.create_grid_view(table=table)
    text_field = data_fixture.create_text_field(table=table)
    long_text_field = data_fixture.create_long_text_field(table=table)
    date_field = data_fixture.create_date_field(
        table=table, date_include_time=True, date_format="ISO"
    )
    number_field = data_fixture.create_number_field(
        table=table,
        number_type="DECIMAL",
        number_negative=True,
        number_decimal_places=2,
    )
    single_select_field = data_fixture.create_single_select_field(table=table)
    option_a = data_fixture.create_select_option(
        field=single_select_field, value="AC", color="blue"
    )
    option_b = data_fixture.create_select_option(
        field=single_select_field, value="BC", color="red"
    )

    handler = ViewHandler()
    model = table.get_model()

    row = model.objects.create(
        **{
            f"field_{text_field.id}": "My name is John Doe.",
            f"field_{long_text_field.id}": "Long text that is not empty.",
            f"field_{date_field.id}": "2020-02-01 01:23",
            f"field_{number_field.id}": "98989898",
            f"field_{single_select_field.id}": option_a,
        }
    )
    row_2 = model.objects.create(
        **{
            f"field_{text_field.id}": "",
            f"field_{long_text_field.id}": "",
            f"field_{date_field.id}": None,
            f"field_{number_field.id}": None,
            f"field_{single_select_field.id}": None,
        }
    )
    row_3 = model.objects.create(
        **{
            f"field_{text_field.id}": "This is a test field.",
            f"field_{long_text_field.id}": "This text is a bit longer, but it also "
            "contains.\n A multiline approach.",
            f"field_{date_field.id}": "0001-01-01 00:12",
            f"field_{number_field.id}": "10000",
            f"field_{single_select_field.id}": option_b,
        }
    )

    filter = data_fixture.create_view_filter(
        view=grid_view, field=text_field, type="contains_not", value="john"
    )
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 2
    assert row_2.id in ids
    assert row_3.id in ids

    filter.value = "DOE"
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 2
    assert row_2.id in ids
    assert row_3.id in ids

    filter.value = "test"
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 2
    assert row.id in ids
    assert row_2.id in ids

    filter.value = " is "
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 1
    assert row_2.id in ids

    filter.value = ""
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 3

    filter.value = "random"
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 3

    filter.field = long_text_field
    filter.value = "multiLINE"
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 2
    assert row.id in ids
    assert row_2.id in ids

    filter.field = date_field
    filter.value = "2020-02-01"
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 2
    assert row.id not in ids

    filter.field = date_field
    filter.value = "01/02/2020"
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 3

    filter.field = date_field
    filter.value = ""
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 3

    filter.field = number_field
    filter.value = "98"
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 2
    assert row.id not in ids

    filter.field = number_field
    filter.value = ""
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 3

    filter.field = date_field
    filter.value = "00:12"
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 2
    assert row_3.id not in ids

    filter.field = single_select_field
    filter.value = "A"
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 2
    assert row.id not in ids

    filter.field = single_select_field
    filter.value = ""
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 3

    filter.field = single_select_field
    filter.value = "C"
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 1
    assert row_2.id in ids


@pytest.mark.django_db
def test_single_select_equal_filter_type(data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    grid_view = data_fixture.create_grid_view(table=table)
    field = data_fixture.create_single_select_field(table=table)
    option_a = data_fixture.create_select_option(field=field, value="A", color="blue")
    option_b = data_fixture.create_select_option(field=field, value="B", color="red")

    handler = ViewHandler()
    model = table.get_model()

    row_1 = model.objects.create(
        **{
            f"field_{field.id}_id": option_a.id,
        }
    )
    row_2 = model.objects.create(
        **{
            f"field_{field.id}_id": option_b.id,
        }
    )
    model.objects.create(
        **{
            f"field_{field.id}_id": None,
        }
    )

    filter = data_fixture.create_view_filter(
        view=grid_view, field=field, type="single_select_equal", value=""
    )
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 3

    filter.value = str(option_a.id)
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 1
    assert row_1.id in ids

    filter.value = str(option_b.id)
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 1
    assert row_2.id in ids

    filter.value = "-1"
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 0

    filter.value = "Test"
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 3


@pytest.mark.django_db
def test_single_select_equal_filter_type_export_import():
    view_filter_type = view_filter_type_registry.get("single_select_equal")
    id_mapping = {"database_field_select_options": {1: 2}}
    assert view_filter_type.get_export_serialized_value("1") == "1"
    assert view_filter_type.set_import_serialized_value("1", id_mapping) == "2"
    assert view_filter_type.set_import_serialized_value("", id_mapping) == ""
    assert view_filter_type.set_import_serialized_value("wrong", id_mapping) == ""


@pytest.mark.django_db
def test_single_select_not_equal_filter_type(data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    grid_view = data_fixture.create_grid_view(table=table)
    field = data_fixture.create_single_select_field(table=table)
    option_a = data_fixture.create_select_option(field=field, value="A", color="blue")
    option_b = data_fixture.create_select_option(field=field, value="B", color="red")

    handler = ViewHandler()
    model = table.get_model()

    row_1 = model.objects.create(
        **{
            f"field_{field.id}_id": option_a.id,
        }
    )
    row_2 = model.objects.create(
        **{
            f"field_{field.id}_id": option_b.id,
        }
    )
    row_3 = model.objects.create(
        **{
            f"field_{field.id}_id": None,
        }
    )

    filter = data_fixture.create_view_filter(
        view=grid_view, field=field, type="single_select_not_equal", value=""
    )
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 3

    filter.value = str(option_a.id)
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 2
    assert row_2.id in ids
    assert row_3.id in ids

    filter.value = str(option_b.id)
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 2
    assert row_1.id in ids
    assert row_3.id in ids

    filter.value = "-1"
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 3

    filter.value = "Test"
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 3


@pytest.mark.django_db
def test_boolean_filter_type(data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    grid_view = data_fixture.create_grid_view(table=table)
    boolean_field = data_fixture.create_boolean_field(table=table)

    handler = ViewHandler()
    model = table.get_model()

    row = model.objects.create(
        **{
            f"field_{boolean_field.id}": True,
        }
    )
    row_2 = model.objects.create(
        **{
            f"field_{boolean_field.id}": False,
        }
    )

    filter = data_fixture.create_view_filter(
        view=grid_view, field=boolean_field, type="boolean", value="TRUE"
    )
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 1
    assert row.id in ids

    filter.value = "Y"
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 1
    assert row.id in ids

    filter.value = "1"
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 1
    assert row.id in ids

    filter.value = "on"
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 1
    assert row.id in ids

    filter.value = "false"
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 1
    assert row_2.id in ids

    filter.value = "no"
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 1
    assert row_2.id in ids

    filter.value = "off"
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 1
    assert row_2.id in ids

    filter.value = ""
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 1
    assert row_2.id in ids


@pytest.mark.django_db
def test_higher_than_filter_type(data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    grid_view = data_fixture.create_grid_view(table=table)
    integer_field = data_fixture.create_number_field(table=table, number_negative=True)
    decimal_field = data_fixture.create_number_field(
        table=table,
        number_type="DECIMAL",
        number_decimal_places=2,
        number_negative=True,
    )

    handler = ViewHandler()
    model = table.get_model()

    row = model.objects.create(
        **{
            f"field_{integer_field.id}": 10,
            f"field_{decimal_field.id}": 20.20,
        }
    )
    model.objects.create(
        **{
            f"field_{integer_field.id}": None,
            f"field_{decimal_field.id}": None,
        }
    )
    row_3 = model.objects.create(
        **{
            f"field_{integer_field.id}": 99,
            f"field_{decimal_field.id}": 99.99,
        }
    )
    row_4 = model.objects.create(
        **{
            f"field_{integer_field.id}": -10,
            f"field_{decimal_field.id}": -30.33,
        }
    )

    filter = data_fixture.create_view_filter(
        view=grid_view, field=integer_field, type="higher_than", value="1"
    )
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 2
    assert row.id in ids
    assert row_3.id in ids

    filter.value = "9.4444"
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 2
    assert row.id in ids
    assert row_3.id in ids

    filter.value = "9.8"
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 2
    assert row.id in ids
    assert row_3.id in ids

    filter.value = "100"
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 0

    filter.value = "not_number"
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 4

    filter.value = "-5"
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 2
    assert row.id in ids
    assert row_3.id in ids

    filter.value = "-11"
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 3
    assert row.id in ids
    assert row_3.id in ids
    assert row_4.id in ids

    filter.value = "-10"
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 2
    assert row.id in ids
    assert row_3.id in ids

    filter.value = "-9.99999"
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 2
    assert row.id in ids
    assert row_3.id in ids

    filter.field = decimal_field
    filter.value = "9.9999"
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 2
    assert row.id in ids
    assert row_3.id in ids

    filter.field = decimal_field
    filter.value = "20.19999"
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 2
    assert row.id in ids
    assert row_3.id in ids

    filter.field = decimal_field
    filter.value = "20.20001"
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 1
    assert row_3.id in ids

    filter.field = decimal_field
    filter.value = "100"
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 0

    filter.field = decimal_field
    filter.value = "99.98"
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 1
    assert row_3.id in ids

    filter.field = decimal_field
    filter.value = "1000"
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 0

    filter.field = decimal_field
    filter.value = "not_number"
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 4


@pytest.mark.django_db
def test_lower_than_filter_type(data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    grid_view = data_fixture.create_grid_view(table=table)
    integer_field = data_fixture.create_number_field(table=table, number_negative=True)
    decimal_field = data_fixture.create_number_field(
        table=table,
        number_type="DECIMAL",
        number_decimal_places=2,
        number_negative=True,
    )

    handler = ViewHandler()
    model = table.get_model()

    row = model.objects.create(
        **{
            f"field_{integer_field.id}": 10,
            f"field_{decimal_field.id}": 20.20,
        }
    )
    model.objects.create(
        **{
            f"field_{integer_field.id}": None,
            f"field_{decimal_field.id}": None,
        }
    )
    row_3 = model.objects.create(
        **{
            f"field_{integer_field.id}": 99,
            f"field_{decimal_field.id}": 99.99,
        }
    )
    row_4 = model.objects.create(
        **{
            f"field_{integer_field.id}": -10,
            f"field_{decimal_field.id}": -30.33,
        }
    )

    filter = data_fixture.create_view_filter(
        view=grid_view, field=integer_field, type="lower_than", value="1"
    )
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 1
    assert row_4.id in ids

    filter.value = "9.4444"
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 1
    assert row_4.id in ids

    filter.value = "9.8"
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 1
    assert row_4.id in ids

    filter.value = "100"
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 3
    assert row.id in ids
    assert row_3.id in ids
    assert row_4.id in ids

    filter.value = "not_number"
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 4

    filter.value = "-5"
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 1
    assert row_4.id in ids

    filter.value = "-9"
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 1
    assert row_4.id in ids

    filter.value = "-10"
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 0

    filter.value = "-9.99999"
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 1
    assert row_4.id in ids

    filter.field = decimal_field
    filter.value = "9.9999"
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 1
    assert row_4.id in ids

    filter.field = decimal_field
    filter.value = "20.199999"
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 1
    assert row_4.id in ids

    filter.field = decimal_field
    filter.value = "20.20001"
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 2
    assert row.id in ids
    assert row_4.id in ids

    filter.field = decimal_field
    filter.value = "100"
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 3
    assert row.id in ids
    assert row_3.id in ids
    assert row_4.id in ids

    filter.field = decimal_field
    filter.value = "99.98"
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 2
    assert row.id in ids
    assert row_4.id in ids

    filter.field = decimal_field
    filter.value = "1000"
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 3
    assert row.id in ids
    assert row_3.id in ids
    assert row_4.id in ids

    filter.field = decimal_field
    filter.value = "not_number"
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 4


@pytest.mark.django_db
def test_date_equal_filter_type(data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    grid_view = data_fixture.create_grid_view(table=table)
    date_field = data_fixture.create_date_field(table=table)
    date_time_field = data_fixture.create_date_field(
        table=table, date_include_time=True
    )

    handler = ViewHandler()
    model = table.get_model()
    utc = timezone("UTC")

    row = model.objects.create(
        **{
            f"field_{date_field.id}": date(2020, 6, 17),
            f"field_{date_time_field.id}": make_aware(
                datetime(2020, 6, 17, 1, 30, 0), utc
            ),
        }
    )
    row_2 = model.objects.create(
        **{
            f"field_{date_field.id}": date(2019, 1, 1),
            f"field_{date_time_field.id}": make_aware(
                datetime(2020, 6, 17, 1, 30, 5), utc
            ),
        }
    )
    model.objects.create(
        **{f"field_{date_field.id}": None, f"field_{date_time_field.id}": None}
    )
    model.objects.create(
        **{
            f"field_{date_field.id}": date(2010, 1, 1),
            f"field_{date_time_field.id}": make_aware(
                datetime(2010, 2, 4, 2, 45, 45), utc
            ),
        }
    )

    filter = data_fixture.create_view_filter(
        view=grid_view, field=date_field, type="date_equal", value="2020-06-17"
    )
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 1
    assert row.id in ids

    filter.field = date_field
    filter.value = "2019-01-01"
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 1
    assert row_2.id in ids

    filter.field = date_field
    filter.value = "2018-01-01"
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 0

    filter.field = date_field
    filter.value = "2019-01-01 12:00:00"
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 1
    assert row_2.id in ids

    # If an empty value is provided then the filter will not be applied, so we expect
    # all the rows.
    filter.field = date_field
    filter.value = ""
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 4

    filter.field = date_time_field
    filter.value = " 2020-06-17 01:30:00 "
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 1
    assert row.id in ids

    filter.field = date_time_field
    filter.value = "2020-06-17 01:30:05"
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 1
    assert row_2.id in ids

    filter.field = date_time_field
    filter.value = "2020-06-17 01:30:10"
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 0

    filter.field = date_time_field
    filter.value = "2020-06-17"
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 2
    assert row.id in ids
    assert row_2.id in ids

    filter.field = date_time_field
    filter.value = "  2020-06-17  "
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 2
    assert row.id in ids
    assert row_2.id in ids

    # If an empty value is provided then the filter will not be applied, so we expect
    # all the rows.
    filter.field = date_time_field
    filter.value = ""
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 4


@pytest.mark.django_db
def test_date_not_equal_filter_type(data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    grid_view = data_fixture.create_grid_view(table=table)
    date_field = data_fixture.create_date_field(table=table)
    date_time_field = data_fixture.create_date_field(
        table=table, date_include_time=True
    )

    handler = ViewHandler()
    model = table.get_model()
    utc = timezone("UTC")

    row = model.objects.create(
        **{
            f"field_{date_field.id}": date(2020, 6, 17),
            f"field_{date_time_field.id}": make_aware(
                datetime(2020, 6, 17, 1, 30, 0), utc
            ),
        }
    )
    row_2 = model.objects.create(
        **{
            f"field_{date_field.id}": date(2019, 1, 1),
            f"field_{date_time_field.id}": make_aware(
                datetime(2020, 6, 17, 1, 30, 5), utc
            ),
        }
    )
    row_3 = model.objects.create(
        **{f"field_{date_field.id}": None, f"field_{date_time_field.id}": None}
    )
    row_4 = model.objects.create(
        **{
            f"field_{date_field.id}": date(2010, 1, 1),
            f"field_{date_time_field.id}": make_aware(
                datetime(2010, 2, 4, 2, 45, 45), utc
            ),
        }
    )

    filter = data_fixture.create_view_filter(
        view=grid_view, field=date_field, type="date_not_equal", value="2020-06-17"
    )
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 3
    assert row_2.id in ids
    assert row_3.id in ids
    assert row_4.id in ids

    filter.field = date_field
    filter.value = "2019-01-01"
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 3
    assert row.id in ids
    assert row_3.id in ids
    assert row_4.id in ids

    filter.field = date_field
    filter.value = "2018-01-01"
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 4

    filter.field = date_field
    filter.value = "2019-01-01 12:00:00"
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 3
    assert row.id in ids
    assert row_3.id in ids
    assert row_4.id in ids

    # If an empty value is provided then the filter will not be applied, so we expect
    # all the rows.
    filter.field = date_field
    filter.value = ""
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 4

    filter.field = date_time_field
    filter.value = " 2020-06-17 01:30:00 "
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 3
    assert row_2.id in ids
    assert row_3.id in ids
    assert row_4.id in ids

    filter.field = date_time_field
    filter.value = "2020-06-17 01:30:05"
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 3
    assert row_2.id not in ids

    filter.field = date_time_field
    filter.value = "2020-06-17 01:30:10"
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 4

    filter.field = date_time_field
    filter.value = "2020-06-17"
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 2
    assert row_3.id in ids
    assert row_4.id in ids

    filter.field = date_time_field
    filter.value = "  2020-06-17  "
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 2
    assert row_3.id in ids
    assert row_4.id in ids

    # If an empty value is provided then the filter will not be applied, so we expect
    # all the rows.
    filter.field = date_time_field
    filter.value = ""
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 4


@pytest.mark.django_db
def test_empty_filter_type(data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    grid_view = data_fixture.create_grid_view(table=table)
    text_field = data_fixture.create_text_field(table=table)
    long_text_field = data_fixture.create_long_text_field(table=table)
    integer_field = data_fixture.create_number_field(table=table)
    decimal_field = data_fixture.create_number_field(
        table=table, number_type="DECIMAL", number_decimal_places=2
    )
    date_field = data_fixture.create_date_field(table=table)
    date_time_field = data_fixture.create_date_field(
        table=table, date_include_time=True
    )
    boolean_field = data_fixture.create_boolean_field(table=table)
    file_field = data_fixture.create_file_field(table=table)
    single_select_field = data_fixture.create_single_select_field(table=table)
    option_1 = data_fixture.create_select_option(field=single_select_field)

    tmp_table = data_fixture.create_database_table(database=table.database)
    tmp_field = data_fixture.create_text_field(table=tmp_table, primary=True)
    link_row_field = FieldHandler().create_field(
        user=user, table=table, type_name="link_row", link_row_table=tmp_table
    )
    tmp_row = tmp_table.get_model().objects.create(**{f"field_{tmp_field.id}": "Test"})

    handler = ViewHandler()
    model = table.get_model()
    utc = timezone("UTC")

    row = model.objects.create(
        **{
            f"field_{text_field.id}": "",
            f"field_{long_text_field.id}": "",
            f"field_{integer_field.id}": None,
            f"field_{decimal_field.id}": None,
            f"field_{date_field.id}": None,
            f"field_{date_time_field.id}": None,
            f"field_{boolean_field.id}": False,
            f"field_{file_field.id}": [],
            f"field_{single_select_field.id}_id": None,
        }
    )
    row_2 = model.objects.create(
        **{
            f"field_{text_field.id}": "Value",
            f"field_{long_text_field.id}": "Value",
            f"field_{integer_field.id}": 10,
            f"field_{decimal_field.id}": 1022,
            f"field_{date_field.id}": date(2020, 6, 17),
            f"field_{date_time_field.id}": make_aware(
                datetime(2020, 6, 17, 1, 30, 0), utc
            ),
            f"field_{boolean_field.id}": True,
            f"field_{file_field.id}": [{"name": "test_file.png"}],
            f"field_{single_select_field.id}_id": option_1.id,
        }
    )
    getattr(row_2, f"field_{link_row_field.id}").add(tmp_row.id)
    row_3 = model.objects.create(
        **{
            f"field_{text_field.id}": " ",
            f"field_{long_text_field.id}": " ",
            f"field_{integer_field.id}": 0,
            f"field_{decimal_field.id}": 0.00,
            f"field_{date_field.id}": date(1970, 1, 1),
            f"field_{date_time_field.id}": make_aware(
                datetime(1970, 1, 1, 0, 0, 0), utc
            ),
            f"field_{boolean_field.id}": True,
            f"field_{file_field.id}": [
                {"name": "test_file.png"},
                {"name": "another_file.jpg"},
            ],
            f"field_{single_select_field.id}_id": option_1.id,
        }
    )
    getattr(row_3, f"field_{link_row_field.id}").add(tmp_row.id)

    filter = data_fixture.create_view_filter(
        view=grid_view, field=text_field, type="empty", value=""
    )
    assert handler.apply_filters(grid_view, model.objects.all()).get().id == row.id

    filter.field = long_text_field
    filter.save()
    assert handler.apply_filters(grid_view, model.objects.all()).get().id == row.id

    filter.field = integer_field
    filter.save()
    assert handler.apply_filters(grid_view, model.objects.all()).get().id == row.id

    filter.field = decimal_field
    filter.save()
    assert handler.apply_filters(grid_view, model.objects.all()).get().id == row.id

    filter.field = date_field
    filter.save()
    assert handler.apply_filters(grid_view, model.objects.all()).get().id == row.id

    filter.field = date_time_field
    filter.save()
    assert handler.apply_filters(grid_view, model.objects.all()).get().id == row.id

    filter.field = link_row_field
    filter.save()
    assert handler.apply_filters(grid_view, model.objects.all()).get().id == row.id

    filter.field = boolean_field
    filter.save()
    assert handler.apply_filters(grid_view, model.objects.all()).get().id == row.id

    filter.field = file_field
    filter.save()
    assert handler.apply_filters(grid_view, model.objects.all()).get().id == row.id

    filter.field = single_select_field
    filter.save()
    assert handler.apply_filters(grid_view, model.objects.all()).get().id == row.id


@pytest.mark.django_db
def test_not_empty_filter_type(data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    grid_view = data_fixture.create_grid_view(table=table)
    text_field = data_fixture.create_text_field(table=table)
    long_text_field = data_fixture.create_long_text_field(table=table)
    integer_field = data_fixture.create_number_field(table=table)
    decimal_field = data_fixture.create_number_field(
        table=table, number_type="DECIMAL", number_decimal_places=2
    )
    date_field = data_fixture.create_date_field(table=table)
    date_time_field = data_fixture.create_date_field(
        table=table, date_include_time=True
    )
    boolean_field = data_fixture.create_boolean_field(table=table)
    file_field = data_fixture.create_file_field(table=table)
    single_select_field = data_fixture.create_single_select_field(table=table)
    option_1 = data_fixture.create_select_option(field=single_select_field)

    tmp_table = data_fixture.create_database_table(database=table.database)
    tmp_field = data_fixture.create_text_field(table=tmp_table, primary=True)
    link_row_field = FieldHandler().create_field(
        user=user, table=table, type_name="link_row", link_row_table=tmp_table
    )
    tmp_row = tmp_table.get_model().objects.create(**{f"field_{tmp_field.id}": "Test"})

    handler = ViewHandler()
    model = table.get_model()
    utc = timezone("UTC")

    model.objects.create(
        **{
            f"field_{text_field.id}": "",
            f"field_{long_text_field.id}": "",
            f"field_{integer_field.id}": None,
            f"field_{decimal_field.id}": None,
            f"field_{date_field.id}": None,
            f"field_{date_time_field.id}": None,
            f"field_{boolean_field.id}": False,
            f"field_{file_field.id}": [],
            f"field_{single_select_field.id}": None,
        }
    )
    row_2 = model.objects.create(
        **{
            f"field_{text_field.id}": "Value",
            f"field_{long_text_field.id}": "Value",
            f"field_{integer_field.id}": 10,
            f"field_{decimal_field.id}": 1022,
            f"field_{date_field.id}": date(2020, 6, 17),
            f"field_{date_time_field.id}": make_aware(
                datetime(2020, 6, 17, 1, 30, 0), utc
            ),
            f"field_{boolean_field.id}": True,
            f"field_{file_field.id}": [{"name": "test_file.png"}],
            f"field_{single_select_field.id}_id": option_1.id,
        }
    )
    getattr(row_2, f"field_{link_row_field.id}").add(tmp_row.id)

    filter = data_fixture.create_view_filter(
        view=grid_view, field=text_field, type="not_empty", value=""
    )
    assert handler.apply_filters(grid_view, model.objects.all()).get().id == row_2.id

    filter.field = long_text_field
    filter.save()
    assert handler.apply_filters(grid_view, model.objects.all()).get().id == row_2.id

    filter.field = integer_field
    filter.save()
    assert handler.apply_filters(grid_view, model.objects.all()).get().id == row_2.id

    filter.field = decimal_field
    filter.save()
    assert handler.apply_filters(grid_view, model.objects.all()).get().id == row_2.id

    filter.field = date_field
    filter.save()
    assert handler.apply_filters(grid_view, model.objects.all()).get().id == row_2.id

    filter.field = date_time_field
    filter.save()
    assert handler.apply_filters(grid_view, model.objects.all()).get().id == row_2.id

    filter.field = link_row_field
    filter.save()
    assert handler.apply_filters(grid_view, model.objects.all()).get().id == row_2.id

    filter.field = boolean_field
    filter.save()
    assert handler.apply_filters(grid_view, model.objects.all()).get().id == row_2.id

    filter.field = file_field
    filter.save()
    assert handler.apply_filters(grid_view, model.objects.all()).get().id == row_2.id

    filter.field = single_select_field
    filter.save()
    assert handler.apply_filters(grid_view, model.objects.all()).get().id == row_2.id


@pytest.mark.django_db
def test_filename_contains_filter_type(data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    grid_view = data_fixture.create_grid_view(table=table)
    file_field = data_fixture.create_file_field(table=table)

    handler = ViewHandler()
    model = table.get_model()

    row = model.objects.create(
        **{
            f"field_{file_field.id}": [{"visible_name": "test_file.png"}],
        }
    )
    row_with_multiple_files = model.objects.create(
        **{
            f"field_{file_field.id}": [
                {"visible_name": "test.doc"},
                {"visible_name": "test.txt"},
            ],
        }
    )
    row_with_no_files = model.objects.create(
        **{
            f"field_{file_field.id}": [],
        }
    )

    filter = data_fixture.create_view_filter(
        view=grid_view,
        field=file_field,
        type="filename_contains",
        value="test_file.png",
    )
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 1
    assert row.id in ids

    filter.value = ".jpg"
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 0

    filter.value = ".png"
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 1
    assert row.id in ids

    filter.value = "test."
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 1
    assert row_with_multiple_files.id in ids

    filter.value = ""
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 3
    assert row.id in ids
    assert row_with_multiple_files.id in ids
    assert row_with_no_files.id in ids

    results = model.objects.all().filter_by_fields_object(
        filter_object={
            f"filter__field_{file_field.id}__filename_contains": [".png"],
        },
        filter_type="AND",
    )
    assert len(results) == 1
