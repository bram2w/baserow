from freezegun import freeze_time

import pytest
from datetime import date
from pytz import timezone

from django.utils.timezone import make_aware, datetime

from baserow.contrib.database.views.registries import view_filter_type_registry
from baserow.contrib.database.views.handler import ViewHandler
from baserow.contrib.database.fields.handler import FieldHandler
from baserow.contrib.database.rows.handler import RowHandler
from baserow.contrib.database.views.view_filters import BaseDateFieldLookupFilterType


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

    view_filter = data_fixture.create_view_filter(
        view=grid_view, field=text_field, type="equal", value="Test"
    )
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 1
    assert row.id in ids

    view_filter.field = long_text_field
    view_filter.value = "Long"
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 1
    assert row.id in ids

    view_filter.field = integer_field
    view_filter.value = "10"
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 1
    assert row.id in ids

    # Because the value 'test' cannot be accepted the filter is not applied so it will
    # return all rows.
    view_filter.field = integer_field
    view_filter.value = "test"
    view_filter.save()
    assert handler.apply_filters(grid_view, model.objects.all()).count() == 3

    view_filter.field = decimal_field
    view_filter.value = "20.20"
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 1
    assert row.id in ids

    view_filter.field = boolean_field
    view_filter.value = "1"
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 1
    assert row.id in ids

    view_filter.field = boolean_field
    view_filter.value = "0"
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 2
    assert row_2.id in ids
    assert row_3.id in ids

    view_filter.field = text_field
    view_filter.value = ""
    view_filter.save()
    assert handler.apply_filters(grid_view, model.objects.all()).count() == 3

    view_filter.field = long_text_field
    view_filter.value = ""
    view_filter.save()
    assert handler.apply_filters(grid_view, model.objects.all()).count() == 3

    view_filter.field = integer_field
    view_filter.value = ""
    view_filter.save()
    assert handler.apply_filters(grid_view, model.objects.all()).count() == 3

    view_filter.field = decimal_field
    view_filter.value = ""
    view_filter.save()
    assert handler.apply_filters(grid_view, model.objects.all()).count() == 3

    view_filter.field = boolean_field
    view_filter.value = ""
    view_filter.save()
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

    view_filter = data_fixture.create_view_filter(
        view=grid_view, field=text_field, type="not_equal", value="Test"
    )
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 2
    assert row_2.id in ids
    assert row_3.id in ids

    view_filter.field = long_text_field
    view_filter.value = "Long"
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 2
    assert row_2.id in ids
    assert row_3.id in ids

    view_filter.field = integer_field
    view_filter.value = "10"
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 2
    assert row_2.id in ids
    assert row_3.id in ids

    # Because the value 'test' cannot be accepted the filter is not applied so it will
    # return all rows.
    view_filter.field = integer_field
    view_filter.value = "test"
    view_filter.save()
    assert handler.apply_filters(grid_view, model.objects.all()).count() == 3

    view_filter.field = decimal_field
    view_filter.value = "20.20"
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 2
    assert row_2.id in ids
    assert row_3.id in ids

    view_filter.field = boolean_field
    view_filter.value = "1"
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 2
    assert row_2.id in ids
    assert row_3.id in ids

    view_filter.field = boolean_field
    view_filter.value = "0"
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 1
    assert row.id in ids

    view_filter.field = text_field
    view_filter.value = ""
    view_filter.save()
    assert handler.apply_filters(grid_view, model.objects.all()).count() == 3

    view_filter.field = long_text_field
    view_filter.value = ""
    view_filter.save()
    assert handler.apply_filters(grid_view, model.objects.all()).count() == 3

    view_filter.field = integer_field
    view_filter.value = ""
    view_filter.save()
    assert handler.apply_filters(grid_view, model.objects.all()).count() == 3

    view_filter.field = decimal_field
    view_filter.value = ""
    view_filter.save()
    assert handler.apply_filters(grid_view, model.objects.all()).count() == 3

    view_filter.field = boolean_field
    view_filter.value = ""
    view_filter.save()
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

    view_filter = data_fixture.create_view_filter(
        view=grid_view, field=text_field, type="contains", value="john"
    )
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 1
    assert row.id in ids

    view_filter.value = "DOE"
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 1
    assert row.id in ids

    view_filter.value = "test"
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 1
    assert row_3.id in ids

    view_filter.value = " is "
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 2
    assert row.id in ids
    assert row_3.id in ids

    view_filter.value = ""
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 3

    view_filter.value = "random"
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 0

    view_filter.field = long_text_field
    view_filter.value = "multiLINE"
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 1
    assert row_3.id in ids

    view_filter.field = date_field
    view_filter.value = "2020-02-01"
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 1
    assert row.id in ids

    view_filter.field = date_field
    view_filter.value = "01/02/2020"
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 0

    view_filter.field = date_field
    view_filter.value = ""
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 3

    view_filter.field = number_field
    view_filter.value = "98"
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 1
    assert row.id in ids

    view_filter.field = number_field
    view_filter.value = "0" + str(row.id)
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 0

    view_filter.field = number_field
    view_filter.value = ""
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 3

    view_filter.field = date_field
    view_filter.value = "00:12"
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 1
    assert row_3.id in ids

    view_filter.field = single_select_field
    view_filter.value = "A"
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 1
    assert row.id in ids

    view_filter.field = single_select_field
    view_filter.value = ""
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 3

    view_filter.field = single_select_field
    view_filter.value = "C"
    view_filter.save()
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

    view_filter = data_fixture.create_view_filter(
        view=grid_view, field=text_field, type="contains_not", value="john"
    )
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 2
    assert row_2.id in ids
    assert row_3.id in ids

    view_filter.value = "DOE"
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 2
    assert row_2.id in ids
    assert row_3.id in ids

    view_filter.value = "test"
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 2
    assert row.id in ids
    assert row_2.id in ids

    view_filter.value = " is "
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 1
    assert row_2.id in ids

    view_filter.value = ""
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 3

    view_filter.value = "random"
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 3

    view_filter.field = long_text_field
    view_filter.value = "multiLINE"
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 2
    assert row.id in ids
    assert row_2.id in ids

    view_filter.field = date_field
    view_filter.value = "2020-02-01"
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 2
    assert row.id not in ids

    view_filter.field = date_field
    view_filter.value = "01/02/2020"
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 3

    view_filter.field = date_field
    view_filter.value = ""
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 3

    view_filter.field = number_field
    view_filter.value = "98"
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 2
    assert row.id not in ids

    view_filter.field = number_field
    view_filter.value = ""
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 3

    view_filter.field = date_field
    view_filter.value = "00:12"
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 2
    assert row_3.id not in ids

    view_filter.field = single_select_field
    view_filter.value = "A"
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 2
    assert row.id not in ids

    view_filter.field = single_select_field
    view_filter.value = ""
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 3

    view_filter.field = single_select_field
    view_filter.value = "C"
    view_filter.save()
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

    view_filter = data_fixture.create_view_filter(
        view=grid_view, field=field, type="single_select_equal", value=""
    )
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 3

    view_filter.value = str(option_a.id)
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 1
    assert row_1.id in ids

    view_filter.value = str(option_b.id)
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 1
    assert row_2.id in ids

    view_filter.value = "-1"
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 0

    view_filter.value = "Test"
    view_filter.save()
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

    view_filter = data_fixture.create_view_filter(
        view=grid_view, field=field, type="single_select_not_equal", value=""
    )
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 3

    view_filter.value = str(option_a.id)
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 2
    assert row_2.id in ids
    assert row_3.id in ids

    view_filter.value = str(option_b.id)
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 2
    assert row_1.id in ids
    assert row_3.id in ids

    view_filter.value = "-1"
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 3

    view_filter.value = "Test"
    view_filter.save()
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

    view_filter = data_fixture.create_view_filter(
        view=grid_view, field=boolean_field, type="boolean", value="TRUE"
    )
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 1
    assert row.id in ids

    view_filter.value = "Y"
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 1
    assert row.id in ids

    view_filter.value = "1"
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 1
    assert row.id in ids

    view_filter.value = "on"
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 1
    assert row.id in ids

    view_filter.value = "false"
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 1
    assert row_2.id in ids

    view_filter.value = "no"
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 1
    assert row_2.id in ids

    view_filter.value = "off"
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 1
    assert row_2.id in ids

    view_filter.value = ""
    view_filter.save()
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

    view_filter = data_fixture.create_view_filter(
        view=grid_view, field=integer_field, type="higher_than", value="1"
    )
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 2
    assert row.id in ids
    assert row_3.id in ids

    view_filter.value = "9.4444"
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 2
    assert row.id in ids
    assert row_3.id in ids

    view_filter.value = "9.8"
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 2
    assert row.id in ids
    assert row_3.id in ids

    view_filter.value = "100"
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 0

    view_filter.value = "not_number"
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 4

    view_filter.value = "-5"
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 2
    assert row.id in ids
    assert row_3.id in ids

    view_filter.value = "-11"
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 3
    assert row.id in ids
    assert row_3.id in ids
    assert row_4.id in ids

    view_filter.value = "-10"
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 2
    assert row.id in ids
    assert row_3.id in ids

    view_filter.value = "-9.99999"
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 2
    assert row.id in ids
    assert row_3.id in ids

    view_filter.field = decimal_field
    view_filter.value = "9.9999"
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 2
    assert row.id in ids
    assert row_3.id in ids

    view_filter.field = decimal_field
    view_filter.value = "20.19999"
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 2
    assert row.id in ids
    assert row_3.id in ids

    view_filter.field = decimal_field
    view_filter.value = "20.20001"
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 1
    assert row_3.id in ids

    view_filter.field = decimal_field
    view_filter.value = "100"
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 0

    view_filter.field = decimal_field
    view_filter.value = "99.98"
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 1
    assert row_3.id in ids

    view_filter.field = decimal_field
    view_filter.value = "1000"
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 0

    view_filter.field = decimal_field
    view_filter.value = "not_number"
    view_filter.save()
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

    view_filter = data_fixture.create_view_filter(
        view=grid_view, field=integer_field, type="lower_than", value="1"
    )
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 1
    assert row_4.id in ids

    view_filter.value = "9.4444"
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 1
    assert row_4.id in ids

    view_filter.value = "9.8"
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 1
    assert row_4.id in ids

    view_filter.value = "100"
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 3
    assert row.id in ids
    assert row_3.id in ids
    assert row_4.id in ids

    view_filter.value = "not_number"
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 4

    view_filter.value = "-5"
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 1
    assert row_4.id in ids

    view_filter.value = "-9"
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 1
    assert row_4.id in ids

    view_filter.value = "-10"
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 0

    view_filter.value = "-9.99999"
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 1
    assert row_4.id in ids

    view_filter.field = decimal_field
    view_filter.value = "9.9999"
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 1
    assert row_4.id in ids

    view_filter.field = decimal_field
    view_filter.value = "20.199999"
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 1
    assert row_4.id in ids

    view_filter.field = decimal_field
    view_filter.value = "20.20001"
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 2
    assert row.id in ids
    assert row_4.id in ids

    view_filter.field = decimal_field
    view_filter.value = "100"
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 3
    assert row.id in ids
    assert row_3.id in ids
    assert row_4.id in ids

    view_filter.field = decimal_field
    view_filter.value = "99.98"
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 2
    assert row.id in ids
    assert row_4.id in ids

    view_filter.field = decimal_field
    view_filter.value = "1000"
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 3
    assert row.id in ids
    assert row_3.id in ids
    assert row_4.id in ids

    view_filter.field = decimal_field
    view_filter.value = "not_number"
    view_filter.save()
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

    view_filter = data_fixture.create_view_filter(
        view=grid_view, field=date_field, type="date_equal", value="2020-06-17"
    )
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 1
    assert row.id in ids

    view_filter.field = date_field
    view_filter.value = "2019-01-01"
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 1
    assert row_2.id in ids

    view_filter.field = date_field
    view_filter.value = "2018-01-01"
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 0

    view_filter.field = date_field
    view_filter.value = "2019-01-01 12:00:00"
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 1
    assert row_2.id in ids

    # If an empty value is provided then the filter will not be applied, so we expect
    # all the rows.
    view_filter.field = date_field
    view_filter.value = ""
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 4

    view_filter.field = date_time_field
    view_filter.value = " 2020-06-17 01:30:00 "
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 1
    assert row.id in ids

    view_filter.field = date_time_field
    view_filter.value = "2020-06-17 01:30:05"
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 1
    assert row_2.id in ids

    view_filter.field = date_time_field
    view_filter.value = "2020-06-17 01:30:10"
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 0

    view_filter.field = date_time_field
    view_filter.value = "2020-06-17"
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 2
    assert row.id in ids
    assert row_2.id in ids

    view_filter.field = date_time_field
    view_filter.value = "  2020-06-17  "
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 2
    assert row.id in ids
    assert row_2.id in ids

    # If an empty value is provided then the filter will not be applied, so we expect
    # all the rows.
    view_filter.field = date_time_field
    view_filter.value = ""
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 4


@pytest.mark.django_db
def test_last_modified_date_equal_filter_type(data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    grid_view = data_fixture.create_grid_view(table=table)
    last_modified_field_date = data_fixture.create_last_modified_field(
        table=table, date_include_time=False, timezone="Europe/Berlin"
    )
    last_modified_field_datetime = data_fixture.create_last_modified_field(
        table=table, date_include_time=True, timezone="Europe/Berlin"
    )
    model = table.get_model()

    with freeze_time("2021-08-04 21:59", tz_offset=+2):
        row = model.objects.create(**{})

    with freeze_time("2021-08-04 22:01", tz_offset=+2):
        row_1 = model.objects.create(**{})

    with freeze_time("2021-08-04 23:01", tz_offset=+2):
        row_2 = model.objects.create(**{})

    handler = ViewHandler()
    model = table.get_model()

    filter = data_fixture.create_view_filter(
        view=grid_view,
        field=last_modified_field_datetime,
        type="date_equal",
        value="2021-08-04",
    )
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 1
    assert row.id in ids

    filter.field = last_modified_field_date
    filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 1
    assert row.id in ids
    assert row_1.id not in ids
    assert row_2.id not in ids


@pytest.mark.django_db
def test_last_modified_day_filter_type(data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    grid_view = data_fixture.create_grid_view(table=table)
    last_modified_field_datetime_berlin = data_fixture.create_last_modified_field(
        table=table, date_include_time=True, timezone="Europe/Berlin"
    )
    last_modified_field_datetime_london = data_fixture.create_last_modified_field(
        table=table, date_include_time=True, timezone="Europe/London"
    )
    handler = ViewHandler()
    model = table.get_model()

    def apply_filter():
        return [
            r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()
        ]

    with freeze_time("2021-08-04 21:59"):
        row = model.objects.create(**{})

    with freeze_time("2021-08-04 22:01"):
        row_1 = model.objects.create(**{})

    with freeze_time("2021-08-04 23:01"):
        row_2 = model.objects.create(**{})

    filter = data_fixture.create_view_filter(
        view=grid_view,
        field=last_modified_field_datetime_london,
        type="date_equals_today",
        value="Europe/London",
    )

    with freeze_time("2021-08-04 01:00"):

        # LastModified Column is based on London Time
        # Filter value is based on London Time
        ids = apply_filter()
        assert len(ids) == 2
        assert row.id in ids
        assert row_1.id in ids
        assert row_2.id not in ids

    with freeze_time("2021-08-04 22:59"):

        # LastModified Column is based on London Time
        # Filter value is based on London Time
        ids = apply_filter()
        assert len(ids) == 2
        assert row.id in ids
        assert row_1.id in ids
        assert row_2.id not in ids

    with freeze_time("2021-08-04 23:59"):

        # LastModified Column is based on London Time
        # Filter value is based on London Time
        ids = apply_filter()
        assert len(ids) == 1
        assert row.id not in ids
        assert row_1.id not in ids
        assert row_2.id in ids

    with freeze_time("2021-08-04"):

        # LastModified Column is based on London Time
        # Filter value is based on London Time
        ids = apply_filter()
        assert len(ids) == 2
        assert row.id in ids
        assert row_1.id in ids
        assert row_2.id not in ids

        # LastModified Column is based on London Time
        # Filter value is based on Berlin Time
        filter.value = "Europe/Berlin"
        filter.save()
        ids = apply_filter()
        assert len(ids) == 1
        assert row.id in ids
        assert row_1.id not in ids
        assert row_2.id not in ids

        # LastModified Column is based on Berlin Time
        # Filter value is based on London Time
        filter.field = last_modified_field_datetime_berlin
        filter.value = "Europe/London"
        filter.save()

        ids = apply_filter()
        assert len(ids) == 2
        assert row.id in ids
        assert row_1.id in ids
        assert row_2.id not in ids

        # LastModified Column is based on Berlin Time
        # Filter value is based on Berlin Time
        filter.value = "Europe/Berlin"
        filter.save()
        ids = apply_filter()
        assert len(ids) == 1
        assert row.id in ids
        assert row_1.id not in ids
        assert row_2.id not in ids

    with freeze_time("2021-08-05"):
        # LastModified Column is based on London Time
        # Filter value is based on London Time
        filter.field = last_modified_field_datetime_london
        filter.value = "Europe/London"
        filter.save()
        ids = apply_filter()
        assert len(ids) == 1
        assert row.id not in ids
        assert row_1.id not in ids
        assert row_2.id in ids

        # LastModified Column is based on London Time
        # Filter value is based on Berlin Time
        filter.value = "Europe/Berlin"
        filter.save()
        ids = apply_filter()
        assert len(ids) == 2
        assert row.id not in ids
        assert row_1.id in ids
        assert row_2.id in ids

        # LastModified Column is based on Berlin Time
        # Filter value is based on London Time
        filter.field = last_modified_field_datetime_berlin
        filter.value = "Europe/London"
        filter.save()

        ids = apply_filter()
        assert len(ids) == 1
        assert row.id not in ids
        assert row_1.id not in ids
        assert row_2.id in ids

        # LastModified Column is based on Berlin Time
        # Filter value is based on Berlin Time
        filter.value = "Europe/Berlin"
        filter.save()
        ids = apply_filter()
        assert len(ids) == 2
        assert row.id not in ids
        assert row_1.id in ids
        assert row_2.id in ids


@pytest.mark.django_db
def test_last_modified_month_filter_type(data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    grid_view = data_fixture.create_grid_view(table=table)
    last_modified_field_datetime_berlin = data_fixture.create_last_modified_field(
        table=table, date_include_time=True, timezone="Europe/Berlin"
    )
    last_modified_field_datetime_london = data_fixture.create_last_modified_field(
        table=table, date_include_time=True, timezone="Europe/London"
    )
    handler = ViewHandler()
    model = table.get_model()

    def apply_filter():
        return [
            r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()
        ]

    with freeze_time("2021-08-31 21:59"):
        row = model.objects.create(**{})

    with freeze_time("2021-08-31 22:01"):
        row_1 = model.objects.create(**{})

    with freeze_time("2021-08-31 23:01"):
        row_2 = model.objects.create(**{})

    filter = data_fixture.create_view_filter(
        view=grid_view,
        field=last_modified_field_datetime_london,
        type="date_equals_month",
        value="Europe/London",
    )

    with freeze_time("2021-08-31"):

        # LastModified Column is based on London Time
        # Filter value is based on London Time
        ids = apply_filter()
        assert len(ids) == 2
        assert row.id in ids
        assert row_1.id in ids
        assert row_2.id not in ids

        # LastModified Column is based on London Time
        # Filter value is based on Berlin Time
        filter.value = "Europe/Berlin"
        filter.save()
        ids = apply_filter()
        assert len(ids) == 1
        assert row.id in ids
        assert row_1.id not in ids
        assert row_2.id not in ids

        # LastModified Column is based on Berlin Time
        # Filter value is based on London Time
        filter.field = last_modified_field_datetime_berlin
        filter.value = "Europe/London"
        filter.save()

        ids = apply_filter()
        assert len(ids) == 2
        assert row.id in ids
        assert row_1.id in ids
        assert row_2.id not in ids

        # LastModified Column is based on Berlin Time
        # Filter value is based on Berlin Time
        filter.value = "Europe/Berlin"
        filter.save()
        ids = apply_filter()
        assert len(ids) == 1
        assert row.id in ids
        assert row_1.id not in ids
        assert row_2.id not in ids

    with freeze_time("2021-09-01"):
        # LastModified Column is based on London Time
        # Filter value is based on London Time
        filter.field = last_modified_field_datetime_london
        filter.value = "Europe/London"
        filter.save()
        ids = apply_filter()
        assert len(ids) == 1
        assert row.id not in ids
        assert row_1.id not in ids
        assert row_2.id in ids

        # LastModified Column is based on London Time
        # Filter value is based on Berlin Time
        filter.value = "Europe/Berlin"
        filter.save()
        ids = apply_filter()
        assert len(ids) == 2
        assert row.id not in ids
        assert row_1.id in ids
        assert row_2.id in ids

        # LastModified Column is based on Berlin Time
        # Filter value is based on London Time
        filter.field = last_modified_field_datetime_berlin
        filter.value = "Europe/London"
        filter.save()

        ids = apply_filter()
        assert len(ids) == 1
        assert row.id not in ids
        assert row_1.id not in ids
        assert row_2.id in ids

        # LastModified Column is based on Berlin Time
        # Filter value is based on Berlin Time
        filter.value = "Europe/Berlin"
        filter.save()
        ids = apply_filter()
        assert len(ids) == 2
        assert row.id not in ids
        assert row_1.id in ids
        assert row_2.id in ids


@pytest.mark.django_db
def test_last_modified_year_filter_type(data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    grid_view = data_fixture.create_grid_view(table=table)
    last_modified_field_datetime_berlin = data_fixture.create_last_modified_field(
        table=table, date_include_time=True, timezone="Europe/Berlin"
    )
    last_modified_field_datetime_london = data_fixture.create_last_modified_field(
        table=table, date_include_time=True, timezone="Europe/London"
    )
    handler = ViewHandler()
    model = table.get_model()

    def apply_filter():
        return [
            r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()
        ]

    with freeze_time("2021-12-31 22:59"):
        row = model.objects.create(**{})

    with freeze_time("2021-12-31 23:01"):
        row_1 = model.objects.create(**{})

    with freeze_time("2022-01-01 00:01"):
        row_2 = model.objects.create(**{})

    filter = data_fixture.create_view_filter(
        view=grid_view,
        field=last_modified_field_datetime_london,
        type="date_equals_year",
        value="Europe/London",
    )

    with freeze_time("2021-12-31"):

        # LastModified Column is based on London Time
        # Filter value is based on London Time
        ids = apply_filter()
        assert len(ids) == 2
        assert row.id in ids
        assert row_1.id in ids
        assert row_2.id not in ids

        # LastModified Column is based on London Time
        # Filter value is based on Berlin Time
        filter.value = "Europe/Berlin"
        filter.save()
        ids = apply_filter()
        assert len(ids) == 1
        assert row.id in ids
        assert row_1.id not in ids
        assert row_2.id not in ids

        # LastModified Column is based on Berlin Time
        # Filter value is based on London Time
        filter.field = last_modified_field_datetime_berlin
        filter.value = "Europe/London"
        filter.save()

        ids = apply_filter()
        assert len(ids) == 2
        assert row.id in ids
        assert row_1.id in ids
        assert row_2.id not in ids

        # LastModified Column is based on Berlin Time
        # Filter value is based on Berlin Time
        filter.value = "Europe/Berlin"
        filter.save()
        ids = apply_filter()
        assert len(ids) == 1
        assert row.id in ids
        assert row_1.id not in ids
        assert row_2.id not in ids

    with freeze_time("2022-01-01"):
        # LastModified Column is based on London Time
        # Filter value is based on London Time
        filter.field = last_modified_field_datetime_london
        filter.value = "Europe/London"
        filter.save()
        ids = apply_filter()
        assert len(ids) == 1
        assert row.id not in ids
        assert row_1.id not in ids
        assert row_2.id in ids

        # LastModified Column is based on London Time
        # Filter value is based on Berlin Time
        filter.value = "Europe/Berlin"
        filter.save()
        ids = apply_filter()
        assert len(ids) == 2
        assert row.id not in ids
        assert row_1.id in ids
        assert row_2.id in ids

        # LastModified Column is based on Berlin Time
        # Filter value is based on London Time
        filter.field = last_modified_field_datetime_berlin
        filter.value = "Europe/London"
        filter.save()

        ids = apply_filter()
        assert len(ids) == 1
        assert row.id not in ids
        assert row_1.id not in ids
        assert row_2.id in ids

        # LastModified Column is based on Berlin Time
        # Filter value is based on Berlin Time
        filter.value = "Europe/Berlin"
        filter.save()
        ids = apply_filter()
        assert len(ids) == 2
        assert row.id not in ids
        assert row_1.id in ids
        assert row_2.id in ids


@pytest.mark.django_db
def test_date_day_month_year_filter_type(data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    grid_view = data_fixture.create_grid_view(table=table)
    date_field = data_fixture.create_date_field(table=table)

    handler = ViewHandler()
    model = table.get_model()

    row = model.objects.create(
        **{
            f"field_{date_field.id}": date(2021, 2, 1),
        }
    )
    row_2 = model.objects.create(
        **{
            f"field_{date_field.id}": date(2021, 1, 1),
        }
    )
    row_3 = model.objects.create(
        **{
            f"field_{date_field.id}": date(2021, 1, 2),
        }
    )
    model.objects.create(
        **{
            f"field_{date_field.id}": None,
        }
    )
    model.objects.create(
        **{
            f"field_{date_field.id}": date(2010, 1, 1),
        }
    )

    view_filter = data_fixture.create_view_filter(
        view=grid_view, field=date_field, type="date_equals_today", value="UTC"
    )

    with freeze_time("2021-01-01 01:01"):
        ids = [
            r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()
        ]
        assert len(ids) == 1
        assert row.id not in ids

        view_filter.type = "date_equals_month"
        view_filter.save()

        ids = [
            r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()
        ]
        assert len(ids) == 2
        assert row_2.id in ids
        assert row_3.id in ids

        view_filter.type = "date_equals_year"
        view_filter.save()

        ids = [
            r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()
        ]
        assert len(ids) == 3
        assert row.id in ids
        assert row_2.id in ids
        assert row_3.id in ids

    view_filter.type = "date_equals_today"
    view_filter.save()

    with freeze_time("2021-01-02 01:01"):
        ids = [
            r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()
        ]
        assert len(ids) == 1
        assert row_3.id in ids

        view_filter.value = "Etc/GMT+2"
        view_filter.save()

        ids = [
            r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()
        ]
        assert len(ids) == 1
        assert row.id not in ids

        view_filter.value = "NOT_EXISTING_SO_WILL_BE_UTC"
        view_filter.save()

        ids = [
            r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()
        ]
        assert len(ids) == 1
        assert row_3.id in ids


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

    view_filter = data_fixture.create_view_filter(
        view=grid_view, field=date_field, type="date_not_equal", value="2020-06-17"
    )
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 3
    assert row_2.id in ids
    assert row_3.id in ids
    assert row_4.id in ids

    view_filter.field = date_field
    view_filter.value = "2019-01-01"
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 3
    assert row.id in ids
    assert row_3.id in ids
    assert row_4.id in ids

    view_filter.field = date_field
    view_filter.value = "2018-01-01"
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 4

    view_filter.field = date_field
    view_filter.value = "2019-01-01 12:00:00"
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 3
    assert row.id in ids
    assert row_3.id in ids
    assert row_4.id in ids

    # If an empty value is provided then the filter will not be applied, so we expect
    # all the rows.
    view_filter.field = date_field
    view_filter.value = ""
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 4

    view_filter.field = date_time_field
    view_filter.value = " 2020-06-17 01:30:00 "
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 3
    assert row_2.id in ids
    assert row_3.id in ids
    assert row_4.id in ids

    view_filter.field = date_time_field
    view_filter.value = "2020-06-17 01:30:05"
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 3
    assert row_2.id not in ids

    view_filter.field = date_time_field
    view_filter.value = "2020-06-17 01:30:10"
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 4

    view_filter.field = date_time_field
    view_filter.value = "2020-06-17"
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 2
    assert row_3.id in ids
    assert row_4.id in ids

    view_filter.field = date_time_field
    view_filter.value = "  2020-06-17  "
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 2
    assert row_3.id in ids
    assert row_4.id in ids

    # If an empty value is provided then the filter will not be applied, so we expect
    # all the rows.
    view_filter.field = date_time_field
    view_filter.value = ""
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 4


def test_date_parser_mixin():
    date_parser = BaseDateFieldLookupFilterType()
    date_string = "2021-07-05"
    parsed_date = date_parser.parse_date(date_string)
    assert parsed_date.year == 2021
    assert parsed_date.month == 7
    assert parsed_date.day == 5

    date_string = " 2021-07-06 "
    parsed_date = date_parser.parse_date(date_string)
    assert parsed_date.year == 2021
    assert parsed_date.month == 7
    assert parsed_date.day == 6

    date_string = ""
    with pytest.raises(ValueError):
        date_parser.parse_date(date_string)

    date_string = "2021-15-15"
    with pytest.raises(ValueError):
        date_parser.parse_date(date_string)


@pytest.mark.django_db
def test_date_before_filter_type(data_fixture):
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
            f"field_{date_field.id}": date(2021, 7, 5),
            f"field_{date_time_field.id}": make_aware(
                datetime(2021, 7, 5, 1, 30, 0), utc
            ),
        }
    )
    row_2 = model.objects.create(
        **{
            f"field_{date_field.id}": date(2021, 7, 6),
            f"field_{date_time_field.id}": make_aware(
                datetime(2021, 7, 6, 1, 30, 5), utc
            ),
        }
    )
    row_3 = model.objects.create(
        **{f"field_{date_field.id}": None, f"field_{date_time_field.id}": None}
    )
    row_4 = model.objects.create(
        **{
            f"field_{date_field.id}": date(2021, 8, 1),
            f"field_{date_time_field.id}": make_aware(
                datetime(2021, 8, 1, 2, 45, 45), utc
            ),
        }
    )

    view_filter = data_fixture.create_view_filter(
        view=grid_view, field=date_field, type="date_before", value="2021-07-06"
    )
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 1
    assert row.id in ids

    view_filter.field = date_time_field
    view_filter.value = "2021-07-06"
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 1
    assert row.id in ids

    view_filter.value = ""
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 4
    assert row.id in ids
    assert row_2.id in ids
    assert row_3.id in ids
    assert row_4.id in ids


@pytest.mark.django_db
def test_date_after_filter_type(data_fixture):
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
            f"field_{date_field.id}": date(2021, 7, 5),
            f"field_{date_time_field.id}": make_aware(
                datetime(2021, 7, 5, 1, 30, 0), utc
            ),
        }
    )
    row_2 = model.objects.create(
        **{
            f"field_{date_field.id}": date(2021, 7, 6),
            f"field_{date_time_field.id}": make_aware(
                datetime(2021, 7, 6, 2, 40, 5), utc
            ),
        }
    )
    row_3 = model.objects.create(
        **{f"field_{date_field.id}": None, f"field_{date_time_field.id}": None}
    )
    row_4 = model.objects.create(
        **{
            f"field_{date_field.id}": date(2021, 8, 1),
            f"field_{date_time_field.id}": make_aware(
                datetime(2021, 8, 1, 2, 45, 45), utc
            ),
        }
    )

    view_filter = data_fixture.create_view_filter(
        view=grid_view, field=date_field, type="date_after", value="2021-07-06"
    )
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 1
    assert row_4.id in ids

    view_filter.field = date_time_field
    view_filter.value = "2021-07-06"
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 1
    assert row_4.id in ids

    view_filter.value = ""
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 4
    assert row.id in ids
    assert row_2.id in ids
    assert row_3.id in ids
    assert row_4.id in ids


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
        user=user,
        table=table,
        name="Link row",
        type_name="link_row",
        link_row_table=tmp_table,
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

    view_filter = data_fixture.create_view_filter(
        view=grid_view, field=text_field, type="empty", value=""
    )
    assert handler.apply_filters(grid_view, model.objects.all()).get().id == row.id

    view_filter.field = long_text_field
    view_filter.save()
    assert handler.apply_filters(grid_view, model.objects.all()).get().id == row.id

    view_filter.field = integer_field
    view_filter.save()
    assert handler.apply_filters(grid_view, model.objects.all()).get().id == row.id

    view_filter.field = decimal_field
    view_filter.save()
    assert handler.apply_filters(grid_view, model.objects.all()).get().id == row.id

    view_filter.field = date_field
    view_filter.save()
    assert handler.apply_filters(grid_view, model.objects.all()).get().id == row.id

    view_filter.field = date_time_field
    view_filter.save()
    assert handler.apply_filters(grid_view, model.objects.all()).get().id == row.id

    view_filter.field = link_row_field
    view_filter.save()
    assert handler.apply_filters(grid_view, model.objects.all()).get().id == row.id

    view_filter.field = boolean_field
    view_filter.save()
    assert handler.apply_filters(grid_view, model.objects.all()).get().id == row.id

    view_filter.field = file_field
    view_filter.save()
    assert handler.apply_filters(grid_view, model.objects.all()).get().id == row.id

    view_filter.field = single_select_field
    view_filter.save()
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
        user=user,
        table=table,
        name="Link row",
        type_name="link_row",
        link_row_table=tmp_table,
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

    view_filter = data_fixture.create_view_filter(
        view=grid_view, field=text_field, type="not_empty", value=""
    )
    assert handler.apply_filters(grid_view, model.objects.all()).get().id == row_2.id

    view_filter.field = long_text_field
    view_filter.save()
    assert handler.apply_filters(grid_view, model.objects.all()).get().id == row_2.id

    view_filter.field = integer_field
    view_filter.save()
    assert handler.apply_filters(grid_view, model.objects.all()).get().id == row_2.id

    view_filter.field = decimal_field
    view_filter.save()
    assert handler.apply_filters(grid_view, model.objects.all()).get().id == row_2.id

    view_filter.field = date_field
    view_filter.save()
    assert handler.apply_filters(grid_view, model.objects.all()).get().id == row_2.id

    view_filter.field = date_time_field
    view_filter.save()
    assert handler.apply_filters(grid_view, model.objects.all()).get().id == row_2.id

    view_filter.field = link_row_field
    view_filter.save()
    assert handler.apply_filters(grid_view, model.objects.all()).get().id == row_2.id

    view_filter.field = boolean_field
    view_filter.save()
    assert handler.apply_filters(grid_view, model.objects.all()).get().id == row_2.id

    view_filter.field = file_field
    view_filter.save()
    assert handler.apply_filters(grid_view, model.objects.all()).get().id == row_2.id

    view_filter.field = single_select_field
    view_filter.save()
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

    view_filter = data_fixture.create_view_filter(
        view=grid_view,
        field=file_field,
        type="filename_contains",
        value="test_file.png",
    )
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 1
    assert row.id in ids

    view_filter.value = ".jpg"
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 0

    view_filter.value = ".png"
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 1
    assert row.id in ids

    view_filter.value = "test."
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 1
    assert row_with_multiple_files.id in ids

    view_filter.value = ""
    view_filter.save()
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


@pytest.mark.django_db
def test_has_file_type(data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    grid_view = data_fixture.create_grid_view(table=table)
    file_field = data_fixture.create_file_field(table=table)

    handler = ViewHandler()
    model = table.get_model()

    row_with_single_image = model.objects.create(
        **{
            f"field_{file_field.id}": [
                {"visible_name": "test_file.jpg", "is_image": True}
            ],
        }
    )
    row_with_single_document = model.objects.create(
        **{
            f"field_{file_field.id}": [{"visible_name": "doc.doc", "is_image": False}],
        }
    )
    row_with_multiple_documents = model.objects.create(
        **{
            f"field_{file_field.id}": [
                {"visible_name": "test.doc", "is_image": False},
                {"visible_name": "test.txt", "is_image": False},
                {"visible_name": "test.doc", "is_image": False},
                {"visible_name": "test.txt", "is_image": False},
            ],
        }
    )
    row_with_multiple_images = model.objects.create(
        **{
            f"field_{file_field.id}": [
                {"visible_name": "test.jpg", "is_image": True},
                {"visible_name": "test.png", "is_image": True},
            ],
        }
    )
    row_with_single_image_and_multiple_documents = model.objects.create(
        **{
            f"field_{file_field.id}": [
                {"visible_name": "test_doc.doc", "is_image": False},
                {"visible_name": "test_doc.doc", "is_image": False},
                {"visible_name": "test_image.jpg", "is_image": True},
                {"visible_name": "test_doc.doc", "is_image": False},
            ],
        }
    )
    row_with_single_document_and_multiple_images = model.objects.create(
        **{
            f"field_{file_field.id}": [
                {"visible_name": "image1.jpg", "is_image": True},
                {"visible_name": "image2.png", "is_image": True},
                {"visible_name": "doc.doc", "is_image": False},
                {"visible_name": "image3.jpg", "is_image": True},
            ],
        }
    )
    model.objects.create(**{f"field_{file_field.id}": []})

    view_filter = data_fixture.create_view_filter(
        view=grid_view,
        field=file_field,
        type="has_file_type",
        value="",
    )
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 7

    view_filter.value = "image"
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 4
    assert row_with_single_image.id in ids
    assert row_with_multiple_images.id in ids
    assert row_with_single_image_and_multiple_documents.id in ids
    assert row_with_single_document_and_multiple_images.id in ids

    view_filter.value = "document"
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 4
    assert row_with_single_document.id in ids
    assert row_with_multiple_documents.id in ids
    assert row_with_single_image_and_multiple_documents.id in ids
    assert row_with_single_document_and_multiple_images.id in ids

    data_fixture.create_view_filter(
        view=grid_view,
        field=file_field,
        type="has_file_type",
        value="image",
    )
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 2
    assert row_with_single_image_and_multiple_documents.id in ids
    assert row_with_single_document_and_multiple_images.id in ids


@pytest.mark.django_db
def test_link_row_preload_values(data_fixture, django_assert_num_queries):
    user = data_fixture.create_user()
    database = data_fixture.create_database_application(user=user)
    table = data_fixture.create_database_table(database=database)
    related_table = data_fixture.create_database_table(database=database)
    primary_field = data_fixture.create_text_field(table=table, primary=True)
    related_primary_field = data_fixture.create_text_field(
        table=related_table, primary=True
    )
    grid_view = data_fixture.create_grid_view(table=table)

    field_handler = FieldHandler()
    link_row_field = field_handler.create_field(
        user=user,
        table=table,
        type_name="link_row",
        name="Test",
        link_row_table=related_table,
    )

    row_handler = RowHandler()
    model = table.get_model()
    related_model = related_table.get_model()

    related_row_1 = row_handler.create_row(
        user=user,
        table=related_table,
        model=related_model,
        values={
            f"field_{related_primary_field.id}": "Related row 1",
        },
    )
    row_handler.create_row(
        user=user,
        table=table,
        model=model,
        values={
            f"field_{primary_field.id}": "Row 1",
            f"field_{link_row_field.id}": [related_row_1.id],
        },
    )
    view_filter = data_fixture.create_view_filter(
        view=grid_view,
        field=link_row_field,
        type="link_row_has",
        value=f"",
    )
    assert view_filter.preload_values["display_name"] is None

    view_filter.value = "test"
    view_filter.save()
    assert view_filter.preload_values["display_name"] is None

    view_filter.value = "-1"
    view_filter.save()
    assert view_filter.preload_values["display_name"] is None

    with django_assert_num_queries(4):
        view_filter.value = f"{related_row_1.id}"
        view_filter.save()
        assert view_filter.preload_values["display_name"] == "Related row 1"


@pytest.mark.django_db
def test_link_row_has_filter_type(data_fixture):
    user = data_fixture.create_user()
    database = data_fixture.create_database_application(user=user)
    table = data_fixture.create_database_table(database=database)
    related_table = data_fixture.create_database_table(database=database)
    primary_field = data_fixture.create_text_field(table=table)
    related_primary_field = data_fixture.create_text_field(table=related_table)
    grid_view = data_fixture.create_grid_view(table=table)

    field_handler = FieldHandler()
    link_row_field = field_handler.create_field(
        user=user,
        table=table,
        type_name="link_row",
        name="Test",
        link_row_table=related_table,
    )

    row_handler = RowHandler()
    model = table.get_model()
    related_model = related_table.get_model()

    related_row_1 = row_handler.create_row(
        user=user,
        table=related_table,
        model=related_model,
        values={
            f"field_{related_primary_field.id}": "Related row 1",
        },
    )
    related_row_2 = row_handler.create_row(
        user=user,
        table=related_table,
        model=related_model,
        values={
            f"field_{related_primary_field.id}": "Related row 2",
        },
    )
    related_row_3 = row_handler.create_row(
        user=user,
        table=related_table,
        model=related_model,
        values={
            f"field_{related_primary_field.id}": "Related row 3",
        },
    )

    row_handler.create_row(
        user=user,
        table=table,
        model=model,
        values={
            f"field_{primary_field.id}": "Row 0",
        },
    )
    row_1 = row_handler.create_row(
        user=user,
        table=table,
        model=model,
        values={
            f"field_{primary_field.id}": "Row 1",
            f"field_{link_row_field.id}": [related_row_1.id],
        },
    )
    row_2 = row_handler.create_row(
        user=user,
        table=table,
        model=model,
        values={
            f"field_{primary_field.id}": "Row 2",
            f"field_{link_row_field.id}": [related_row_2.id],
        },
    )
    row_3 = row_handler.create_row(
        user=user,
        table=table,
        model=model,
        values={
            f"field_{primary_field.id}": "Row 3",
            f"field_{link_row_field.id}": [related_row_3.id],
        },
    )
    row_with_all_relations = row_handler.create_row(
        user=user,
        table=table,
        model=model,
        values={
            f"field_{primary_field.id}": "Row 4",
            f"field_{link_row_field.id}": [
                related_row_1.id,
                related_row_2.id,
                related_row_3.id,
            ],
        },
    )

    handler = ViewHandler()
    view_filter = data_fixture.create_view_filter(
        view=grid_view,
        field=link_row_field,
        type="link_row_has",
        value=f"",
    )
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 5

    view_filter.value = "not_number"
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 5

    view_filter.value = "-1"
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 0

    view_filter.value = f"{related_row_1.id}"
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 2
    assert row_1.id in ids
    assert row_with_all_relations.id in ids

    view_filter.value = f"{related_row_2.id}"
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 2
    assert row_2.id in ids
    assert row_with_all_relations.id in ids

    view_filter.value = f"{related_row_3.id}"
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 2
    assert row_3.id in ids
    assert row_with_all_relations.id in ids


@pytest.mark.django_db
def test_link_row_has_not_filter_type(data_fixture):
    user = data_fixture.create_user()
    database = data_fixture.create_database_application(user=user)
    table = data_fixture.create_database_table(database=database)
    related_table = data_fixture.create_database_table(database=database)
    primary_field = data_fixture.create_text_field(table=table)
    related_primary_field = data_fixture.create_text_field(table=related_table)
    grid_view = data_fixture.create_grid_view(table=table)

    field_handler = FieldHandler()
    link_row_field = field_handler.create_field(
        user=user,
        table=table,
        type_name="link_row",
        name="Test",
        link_row_table=related_table,
    )

    row_handler = RowHandler()
    model = table.get_model()
    related_model = related_table.get_model()

    related_row_1 = row_handler.create_row(
        user=user,
        table=related_table,
        model=related_model,
        values={
            f"field_{related_primary_field.id}": "Related row 1",
        },
    )
    related_row_2 = row_handler.create_row(
        user=user,
        table=related_table,
        model=related_model,
        values={
            f"field_{related_primary_field.id}": "Related row 2",
        },
    )
    related_row_3 = row_handler.create_row(
        user=user,
        table=related_table,
        model=related_model,
        values={
            f"field_{related_primary_field.id}": "Related row 3",
        },
    )

    row_handler.create_row(
        user=user,
        table=table,
        model=model,
        values={
            f"field_{primary_field.id}": "Row 0",
        },
    )
    row_1 = row_handler.create_row(
        user=user,
        table=table,
        model=model,
        values={
            f"field_{primary_field.id}": "Row 1",
            f"field_{link_row_field.id}": [related_row_1.id],
        },
    )
    row_2 = row_handler.create_row(
        user=user,
        table=table,
        model=model,
        values={
            f"field_{primary_field.id}": "Row 2",
            f"field_{link_row_field.id}": [related_row_2.id],
        },
    )
    row_3 = row_handler.create_row(
        user=user,
        table=table,
        model=model,
        values={
            f"field_{primary_field.id}": "Row 3",
            f"field_{link_row_field.id}": [related_row_3.id],
        },
    )
    row_with_all_relations = row_handler.create_row(
        user=user,
        table=table,
        model=model,
        values={
            f"field_{primary_field.id}": "Row 4",
            f"field_{link_row_field.id}": [
                related_row_1.id,
                related_row_2.id,
                related_row_3.id,
            ],
        },
    )

    handler = ViewHandler()
    view_filter = data_fixture.create_view_filter(
        view=grid_view,
        field=link_row_field,
        type="link_row_has_not",
        value=f"",
    )
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 5

    view_filter.value = "not_number"
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 5

    view_filter.value = "-1"
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 5

    view_filter.value = f"{related_row_1.id}"
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 3
    assert row_1.id not in ids
    assert row_with_all_relations.id not in ids

    view_filter.value = f"{related_row_2.id}"
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 3
    assert row_2.id not in ids
    assert row_with_all_relations.id not in ids

    view_filter.value = f"{related_row_3.id}"
    view_filter.save()
    ids = [r.id for r in handler.apply_filters(grid_view, model.objects.all()).all()]
    assert len(ids) == 3
    assert row_3.id not in ids
    assert row_with_all_relations.id not in ids
