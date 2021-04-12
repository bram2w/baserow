import pytest

from datetime import datetime

from baserow.contrib.database.fields.models import DateField, LinkRowField


@pytest.mark.django_db
def test_model_class_name(data_fixture):
    field_1 = data_fixture.create_text_field(name="Some test table")
    assert field_1.model_attribute_name == "some_test_table"

    field_2 = data_fixture.create_text_field(name="3 Some test @ table")
    assert field_2.model_attribute_name == "field_3_some_test_table"


@pytest.mark.django_db
def test_date_field_get_python_format():
    eu = DateField(date_format="EU")
    us = DateField(date_format="US")
    iso = DateField(date_format="ISO")

    eu_time_24 = DateField(
        date_format="EU", date_include_time=True, date_time_format="24"
    )
    us_time_24 = DateField(
        date_format="US", date_include_time=True, date_time_format="24"
    )
    iso_time_24 = DateField(
        date_format="ISO", date_include_time=True, date_time_format="24"
    )

    eu_time_12 = DateField(
        date_format="EU", date_include_time=True, date_time_format="12"
    )
    us_time_12 = DateField(
        date_format="US", date_include_time=True, date_time_format="12"
    )
    iso_time_12 = DateField(
        date_format="ISO", date_include_time=True, date_time_format="12"
    )

    assert eu.get_python_format() == "%d/%m/%Y"
    assert us.get_python_format() == "%m/%d/%Y"
    assert iso.get_python_format() == "%Y-%m-%d"

    assert eu_time_24.get_python_format() == "%d/%m/%Y %H:%M"
    assert us_time_24.get_python_format() == "%m/%d/%Y %H:%M"
    assert iso_time_24.get_python_format() == "%Y-%m-%d %H:%M"

    assert eu_time_12.get_python_format() == "%d/%m/%Y %I:%M %p"
    assert us_time_12.get_python_format() == "%m/%d/%Y %I:%M %p"
    assert iso_time_12.get_python_format() == "%Y-%m-%d %I:%M %p"

    d = datetime(2020, 10, 1, 14, 30, 30)

    assert d.strftime(eu.get_python_format()) == "01/10/2020"
    assert d.strftime(us.get_python_format()) == "10/01/2020"
    assert d.strftime(iso.get_python_format()) == "2020-10-01"

    assert d.strftime(eu_time_24.get_python_format()) == "01/10/2020 14:30"
    assert d.strftime(us_time_24.get_python_format()) == "10/01/2020 14:30"
    assert d.strftime(iso_time_24.get_python_format()) == "2020-10-01 14:30"

    assert d.strftime(eu_time_12.get_python_format()) == "01/10/2020 02:30 PM"
    assert d.strftime(us_time_12.get_python_format()) == "10/01/2020 02:30 PM"
    assert d.strftime(iso_time_12.get_python_format()) == "2020-10-01 02:30 PM"


@pytest.mark.django_db
def test_link_row_field(data_fixture):
    table = data_fixture.create_database_table()
    table_2 = data_fixture.create_database_table(database=table.database)

    assert (
        LinkRowField.objects.create(
            name="Test1", table=table, link_row_table=table_2, order=1
        ).link_row_relation_id
        == 1
    )
    assert (
        LinkRowField.objects.create(
            name="Test1", table=table, link_row_table=table_2, order=1
        ).link_row_relation_id
        == 2
    )
    assert (
        LinkRowField.objects.create(
            name="Test1", table=table, link_row_table=table_2, order=1
        ).link_row_relation_id
        == 3
    )

    field = LinkRowField.objects.create(
        name="Test1", table=table, link_row_table=table_2, order=1
    )
    field.link_row_relation_id = 100
    field.save()

    assert field.through_table_name == "database_relation_100"

    assert (
        LinkRowField.objects.create(
            name="Test1", table=table, link_row_table=table_2, order=1
        ).link_row_relation_id
        == 101
    )
