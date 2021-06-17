from io import BytesIO
from unittest.mock import patch

import pytest
from django.utils.dateparse import parse_date, parse_datetime
from django.utils.timezone import utc, make_aware

from baserow.contrib.database.export.handler import ExportHandler
from baserow.contrib.database.rows.handler import RowHandler
from tests.test_utils import setup_interesting_test_table


def _parse_datetime(datetime):
    return make_aware(parse_datetime(datetime), timezone=utc)


def _parse_date(date):
    return parse_date(date)


@pytest.mark.django_db
@patch("baserow.contrib.database.export.handler.default_storage")
def test_can_export_every_interesting_different_field_to_json(
    storage_mock, data_fixture
):
    contents = run_export_over_interesting_test_table(
        data_fixture, storage_mock, {"exporter_type": "json"}
    )
    assert (
        contents
        == """[
{
    "id": 1,
    "text": "",
    "long_text": "",
    "url": "",
    "email": "",
    "negative_int": "",
    "positive_int": "",
    "negative_decimal": "",
    "positive_decimal": "",
    "boolean": false,
    "datetime_us": "",
    "date_us": "",
    "datetime_eu": "",
    "date_eu": "",
    "link_row": [],
    "decimal_link_row": [],
    "file_link_row": [],
    "file": [],
    "single_select": "",
    "phone_number": ""
},
{
    "id": 2,
    "text": "text",
    "long_text": "long_text",
    "url": "https://www.google.com",
    "email": "test@example.com",
    "negative_int": -1,
    "positive_int": 1,
    "negative_decimal": "-1.2",
    "positive_decimal": "1.2",
    "boolean": true,
    "datetime_us": "02/01/2020 01:23",
    "date_us": "02/01/2020",
    "datetime_eu": "01/02/2020 01:23",
    "date_eu": "01/02/2020",
    "link_row": [
        "linked_row_1",
        "linked_row_2",
        "unnamed row 3"
    ],
    "decimal_link_row": [
        "1.234",
        "-123.456",
        "unnamed row 3"
    ],
    "file_link_row": [
        [
            {
                "visible_name": "name.txt",
                "url": "http://localhost:8000/media/user_files/test_hash.txt"
            }
        ],
        "unnamed row 2"
    ],
    "file": [
        {
            "visible_name": "a.txt",
            "url": "http://localhost:8000/media/user_files/hashed_name.txt"
        },
        {
            "visible_name": "b.txt",
            "url": "http://localhost:8000/media/user_files/other_name.txt"
        }
    ],
    "single_select": "A",
    "phone_number": "+4412345678"
}
]
"""
    )


@pytest.mark.django_db
@patch("baserow.contrib.database.export.handler.default_storage")
def test_if_duplicate_field_names_json_export(storage_mock, data_fixture):
    user = data_fixture.create_user()
    database = data_fixture.create_database_application(user=user)
    table = data_fixture.create_database_table(database=database)
    data_fixture.create_text_field(table=table, name="name", order=1)
    data_fixture.create_text_field(table=table, name="name", order=2)
    data_fixture.create_text_field(table=table, name="name", order=3)
    data_fixture.create_text_field(table=table, name='Another"name', order=4)
    data_fixture.create_text_field(table=table, name='Another"name', order=5)
    row_handler = RowHandler()
    row_handler.create_row(user=user, table=table)
    job, contents = run_export_job_with_mock_storage(
        table, None, storage_mock, user, {"exporter_type": "json"}
    )
    assert (
        contents
        == """[
{
    "id": 1,
    "name": "",
    "name 2": "",
    "name 3": "",
    "Another\\"name": "",
    "Another\\"name 2": ""
}
]
"""
    )


@pytest.mark.django_db
@patch("baserow.contrib.database.export.handler.default_storage")
def test_can_export_every_interesting_different_field_to_xml(
    storage_mock, data_fixture
):
    xml = run_export_over_interesting_test_table(
        data_fixture, storage_mock, {"exporter_type": "xml"}
    )
    expected_xml = f"""<?xml version="1.0" encoding="utf-8" ?>
<rows>
<row>
    <id>1</id>
    <text/>
    <long-text/>
    <url/>
    <email/>
    <negative-int/>
    <positive-int/>
    <negative-decimal/>
    <positive-decimal/>
    <boolean>false</boolean>
    <datetime-us/>
    <date-us/>
    <datetime-eu/>
    <date-eu/>
    <link-row/>
    <decimal-link-row/>
    <file-link-row/>
    <file/>
    <single-select/>
    <phone-number/>
</row>
<row>
    <id>2</id>
    <text>text</text>
    <long-text>long_text</long-text>
    <url>https://www.google.com</url>
    <email>test@example.com</email>
    <negative-int>-1</negative-int>
    <positive-int>1</positive-int>
    <negative-decimal>-1.2</negative-decimal>
    <positive-decimal>1.2</positive-decimal>
    <boolean>true</boolean>
    <datetime-us>02/01/2020 01:23</datetime-us>
    <date-us>02/01/2020</date-us>
    <datetime-eu>01/02/2020 01:23</datetime-eu>
    <date-eu>01/02/2020</date-eu>
    <link-row>
        <item>linked_row_1</item>
        <item>linked_row_2</item>
        <item>unnamed row 3</item>
    </link-row>
    <decimal-link-row>
        <item>1.234</item>
        <item>-123.456</item>
        <item>unnamed row 3</item>
    </decimal-link-row>
    <file-link-row>
        <item>
            <item>
                <visible_name>name.txt</visible_name>
                <url>http://localhost:8000/media/user_files/test_hash.txt</url>
            </item>
        </item>
        <item>
            unnamed row 2
        </item>
    </file-link-row>
    <file>
        <item>
            <visible_name>a.txt</visible_name>
            <url>http://localhost:8000/media/user_files/hashed_name.txt</url>
        </item>
        <item>
            <visible_name>b.txt</visible_name>
            <url>http://localhost:8000/media/user_files/other_name.txt</url>
        </item>
    </file>
    <single-select>A</single-select>
    <phone-number>+4412345678</phone-number>
</row>
</rows>
"""
    assert strip_indents_and_newlines(xml) == strip_indents_and_newlines(expected_xml)


@pytest.mark.django_db
@patch("baserow.contrib.database.export.handler.default_storage")
def test_if_xml_duplicate_name_and_value_are_escaped(storage_mock, data_fixture):
    user = data_fixture.create_user()
    database = data_fixture.create_database_application(user=user)
    table = data_fixture.create_database_table(database=database)
    text = data_fixture.create_text_field(table=table, name="<name>", order=0)
    data_fixture.create_text_field(table=table, name="name", order=1)
    data_fixture.create_text_field(table=table, name="Another name", order=2)
    data_fixture.create_text_field(table=table, name="Another@name", order=3)
    empty_1 = data_fixture.create_text_field(table=table, name="@", order=4)
    empty_2 = data_fixture.create_text_field(table=table, name="", order=5)
    data_fixture.create_text_field(table=table, name="1", order=6)
    row_handler = RowHandler()
    row_handler.create_row(
        user=user,
        table=table,
        values={f"field_{text.id}": "<value>"},
    )
    job, contents = run_export_job_with_mock_storage(
        table, None, storage_mock, user, {"exporter_type": "xml"}
    )
    assert strip_indents_and_newlines(contents) == strip_indents_and_newlines(
        f"""
<?xml version="1.0" encoding="utf-8" ?>
<rows>
  <row>
    <id>1</id>
    <name>&lt;value&gt;</name>
    <name-2/>
    <Another-name/>
    <Another-name-2/>
    <field-{empty_1.id}/>
    <field-{empty_2.id}/>
    <field-1/>
  </row>
</rows>
"""
    )


def strip_indents_and_newlines(xml):
    return "".join([line.strip() for line in xml.split("\n")])


def run_export_over_interesting_test_table(data_fixture, storage_mock, options):
    table, user = setup_interesting_test_table(data_fixture)
    grid_view = data_fixture.create_grid_view(table=table)
    job, contents = run_export_job_with_mock_storage(
        table, grid_view, storage_mock, user, options
    )
    return contents


def run_export_job_with_mock_storage(
    table, grid_view, storage_mock, user, options=None
):
    if options is None:
        options = {"exporter_type": "csv"}

    if "export_charset" not in options:
        options["export_charset"] = "utf-8"

    stub_file = BytesIO()
    storage_mock.open.return_value = stub_file
    close = stub_file.close
    stub_file.close = lambda: None
    handler = ExportHandler()
    job = handler.create_pending_export_job(user, table, grid_view, options)
    handler.run_export_job(job)
    actual = stub_file.getvalue().decode(options["export_charset"])
    close()
    return job, actual
