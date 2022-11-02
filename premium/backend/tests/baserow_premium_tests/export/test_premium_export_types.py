from io import BytesIO
from unittest.mock import patch

from django.test.utils import override_settings
from django.utils.dateparse import parse_date, parse_datetime
from django.utils.timezone import make_aware, utc

import pytest
from baserow_premium.license.exceptions import FeaturesNotAvailableError

from baserow.contrib.database.export.handler import ExportHandler
from baserow.contrib.database.rows.handler import RowHandler
from baserow.test_utils.helpers import setup_interesting_test_table


def _parse_datetime(datetime):
    return make_aware(parse_datetime(datetime), timezone=utc)


def _parse_date(date):
    return parse_date(date)


@pytest.mark.django_db
@override_settings(DEBUG=True)
@patch("baserow.contrib.database.export.handler.default_storage")
def test_can_export_every_interesting_different_field_to_json(
    storage_mock, premium_data_fixture
):
    contents = run_export_over_interesting_test_table(
        premium_data_fixture,
        storage_mock,
        {"exporter_type": "json"},
        user_kwargs={"has_active_premium_license": True},
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
    "rating": 0,
    "boolean": false,
    "datetime_us": "",
    "date_us": "",
    "datetime_eu": "",
    "date_eu": "",
    "last_modified_datetime_us": "01/02/2021 13:00",
    "last_modified_date_us": "01/02/2021",
    "last_modified_datetime_eu": "02/01/2021 13:00",
    "last_modified_date_eu": "02/01/2021",
    "created_on_datetime_us": "01/02/2021 13:00",
    "created_on_date_us": "01/02/2021",
    "created_on_datetime_eu": "02/01/2021 13:00",
    "created_on_date_eu": "02/01/2021",
    "link_row": [],
    "self_link_row": [],
    "link_row_without_related": [],
    "decimal_link_row": [],
    "file_link_row": [],
    "file": [],
    "single_select": "",
    "multiple_select": [],
    "multiple_collaborators": [],
    "phone_number": "",
    "formula_text": "test FORMULA",
    "formula_int": 1,
    "formula_bool": true,
    "formula_decimal": "33.3333333333",
    "formula_dateinterval": "1 day",
    "formula_date": "2020-01-01",
    "formula_singleselect": "",
    "formula_email": "",
    "formula_link_with_label": {
        "url": "https://google.com",
        "label": "label"
    },
    "formula_link_url_only": {
        "url": "https://google.com"
    },
    "lookup": []
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
    "rating": 3,
    "boolean": true,
    "datetime_us": "02/01/2020 01:23",
    "date_us": "02/01/2020",
    "datetime_eu": "01/02/2020 01:23",
    "date_eu": "01/02/2020",
    "last_modified_datetime_us": "01/02/2021 13:00",
    "last_modified_date_us": "01/02/2021",
    "last_modified_datetime_eu": "02/01/2021 13:00",
    "last_modified_date_eu": "02/01/2021",
    "created_on_datetime_us": "01/02/2021 13:00",
    "created_on_date_us": "01/02/2021",
    "created_on_datetime_eu": "02/01/2021 13:00",
    "created_on_date_eu": "02/01/2021",
    "link_row": [
        "linked_row_1",
        "linked_row_2",
        "unnamed row 3"
    ],
    "self_link_row": [
        "unnamed row 1"
    ],
    "link_row_without_related": [
        "linked_row_1",
        "linked_row_2"
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
    "multiple_select": [
        "D",
        "C",
        "E"
    ],
    "multiple_collaborators": [
        "user2@example.com",
        "user3@example.com"
    ],
    "phone_number": "+4412345678",
    "formula_text": "test FORMULA",
    "formula_int": 1,
    "formula_bool": true,
    "formula_decimal": "33.3333333333",
    "formula_dateinterval": "1 day",
    "formula_date": "2020-01-01",
    "formula_singleselect": "A",
    "formula_email": "test@example.com",
    "formula_link_with_label": {
        "url": "https://google.com",
        "label": "label"
    },
    "formula_link_url_only": {
        "url": "https://google.com"
    },
    "lookup": [
        "linked_row_1",
        "linked_row_2",
        ""
    ]
}
]
"""
    )


@pytest.mark.django_db
@override_settings(DEBUG=True)
@patch("baserow.contrib.database.export.handler.default_storage")
def test_cannot_export_json_without_premium_license(storage_mock, premium_data_fixture):
    with pytest.raises(FeaturesNotAvailableError):
        run_export_over_interesting_test_table(
            premium_data_fixture, storage_mock, {"exporter_type": "json"}
        )


@pytest.mark.django_db
@override_settings(DEBUG=True)
@patch("baserow.contrib.database.export.handler.default_storage")
def test_cannot_export_json_without_premium_license_for_group(
    storage_mock, premium_data_fixture, alternative_per_group_license_service
):
    # Setting the group id to `0` will make sure that the user doesn't have
    # premium access to the group.
    user = premium_data_fixture.create_user(has_active_premium_license=True)
    alternative_per_group_license_service.restrict_user_premium_to(user, [0])
    with pytest.raises(FeaturesNotAvailableError):
        run_export_over_interesting_test_table(
            premium_data_fixture, storage_mock, {"exporter_type": "json"}, user=user
        )


@pytest.mark.django_db
@override_settings(DEBUG=True)
@patch("baserow.contrib.database.export.handler.default_storage")
def test_if_duplicate_field_names_json_export(storage_mock, premium_data_fixture):
    user = premium_data_fixture.create_user(has_active_premium_license=True)
    database = premium_data_fixture.create_database_application(user=user)
    table = premium_data_fixture.create_database_table(database=database)
    premium_data_fixture.create_text_field(table=table, name="name", order=1)
    premium_data_fixture.create_text_field(table=table, name="name", order=2)
    premium_data_fixture.create_text_field(table=table, name="name", order=3)
    premium_data_fixture.create_text_field(table=table, name='Another"name', order=4)
    premium_data_fixture.create_text_field(table=table, name='Another"name', order=5)
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
@override_settings(DEBUG=True)
@patch("baserow.contrib.database.export.handler.default_storage")
def test_can_export_every_interesting_different_field_to_xml(
    storage_mock, premium_data_fixture
):
    xml = run_export_over_interesting_test_table(
        premium_data_fixture,
        storage_mock,
        {"exporter_type": "xml"},
        user_kwargs={"has_active_premium_license": True},
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
    <rating>0</rating>
    <boolean>false</boolean>
    <datetime-us/>
    <date-us/>
    <datetime-eu/>
    <date-eu/>
    <last-modified-datetime-us>01/02/2021 13:00</last-modified-datetime-us>
    <last-modified-date-us>01/02/2021</last-modified-date-us>
    <last-modified-datetime-eu>02/01/2021 13:00</last-modified-datetime-eu>
    <last-modified-date-eu>02/01/2021</last-modified-date-eu>
    <created-on-datetime-us>01/02/2021 13:00</created-on-datetime-us>
    <created-on-date-us>01/02/2021</created-on-date-us>
    <created-on-datetime-eu>02/01/2021 13:00</created-on-datetime-eu>
    <created-on-date-eu>02/01/2021</created-on-date-eu>
    <link-row/>
    <self-link-row/>
    <link-row-without-related/>
    <decimal-link-row/>
    <file-link-row/>
    <file/>
    <single-select/>
    <multiple-select/>
    <multiple-collaborators/>
    <phone-number/>
    <formula-text>test FORMULA</formula-text>
    <formula-int>1</formula-int>
    <formula-bool>true</formula-bool>
    <formula-decimal>33.3333333333</formula-decimal>
    <formula-dateinterval>1 day</formula-dateinterval>
    <formula-date>2020-01-01</formula-date>
    <formula-singleselect/>
    <formula-email/>
    <formula-link-with-label>
        <url>https://google.com</url>
        <label>label</label>
    </formula-link-with-label>
    <formula-link-url-only>
        <url>https://google.com</url>
    </formula-link-url-only>
    <lookup/>
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
    <rating>3</rating>
    <boolean>true</boolean>
    <datetime-us>02/01/2020 01:23</datetime-us>
    <date-us>02/01/2020</date-us>
    <datetime-eu>01/02/2020 01:23</datetime-eu>
    <date-eu>01/02/2020</date-eu>
    <last-modified-datetime-us>01/02/2021 13:00</last-modified-datetime-us>
    <last-modified-date-us>01/02/2021</last-modified-date-us>
    <last-modified-datetime-eu>02/01/2021 13:00</last-modified-datetime-eu>
    <last-modified-date-eu>02/01/2021</last-modified-date-eu>
    <created-on-datetime-us>01/02/2021 13:00</created-on-datetime-us>
    <created-on-date-us>01/02/2021</created-on-date-us>
    <created-on-datetime-eu>02/01/2021 13:00</created-on-datetime-eu>
    <created-on-date-eu>02/01/2021</created-on-date-eu>
    <link-row>
        <item>linked_row_1</item>
        <item>linked_row_2</item>
        <item>unnamed row 3</item>
    </link-row>
    <self-link-row>
        <item>unnamed row 1</item>
    </self-link-row>
    <link-row-without-related>
        <item>linked_row_1</item>
        <item>linked_row_2</item>
    </link-row-without-related>
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
    <multiple-select>
        <item>D</item>
        <item>C</item>
        <item>E</item>
    </multiple-select>
    <multiple-collaborators>
        <item>user2@example.com</item>
        <item>user3@example.com</item>
    </multiple-collaborators>
    <phone-number>+4412345678</phone-number>
    <formula-text>test FORMULA</formula-text>
    <formula-int>1</formula-int>
    <formula-bool>true</formula-bool>
    <formula-decimal>33.3333333333</formula-decimal>
    <formula-dateinterval>1 day</formula-dateinterval>
    <formula-date>2020-01-01</formula-date>
    <formula-singleselect>A</formula-singleselect>
    <formula-email>test@example.com</formula-email>
    <formula-link-with-label>
        <url>https://google.com</url>
        <label>label</label>
    </formula-link-with-label>
    <formula-link-url-only>
        <url>https://google.com</url>
    </formula-link-url-only>
    <lookup><item>linked_row_1</item><item>linked_row_2</item><item/></lookup>
</row>
</rows>
"""
    assert strip_indents_and_newlines(xml) == strip_indents_and_newlines(expected_xml)


@pytest.mark.django_db
@override_settings(DEBUG=True)
@patch("baserow.contrib.database.export.handler.default_storage")
def test_if_xml_duplicate_name_and_value_are_escaped(
    storage_mock, premium_data_fixture
):
    user = premium_data_fixture.create_user(has_active_premium_license=True)
    database = premium_data_fixture.create_database_application(user=user)
    table = premium_data_fixture.create_database_table(database=database)
    text = premium_data_fixture.create_text_field(table=table, name="<name>", order=0)
    premium_data_fixture.create_text_field(table=table, name="name", order=1)
    premium_data_fixture.create_text_field(table=table, name="Another name", order=2)
    premium_data_fixture.create_text_field(table=table, name="Another@name", order=3)
    empty_1 = premium_data_fixture.create_text_field(table=table, name="@", order=4)
    empty_2 = premium_data_fixture.create_text_field(table=table, name="", order=5)
    premium_data_fixture.create_text_field(table=table, name="1", order=6)
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


@pytest.mark.django_db
@override_settings(DEBUG=True)
@patch("baserow.contrib.database.export.handler.default_storage")
def test_cannot_export_xml_without_premium_license(storage_mock, premium_data_fixture):
    with pytest.raises(FeaturesNotAvailableError):
        run_export_over_interesting_test_table(
            premium_data_fixture, storage_mock, {"exporter_type": "xml"}
        )


@pytest.mark.django_db
@override_settings(DEBUG=True)
@patch("baserow.contrib.database.export.handler.default_storage")
def test_cannot_export_xml_without_premium_license_for_group(
    storage_mock, premium_data_fixture, alternative_per_group_license_service
):
    # Setting the group id to `0` will make sure that the user doesn't have
    # premium access to the group.
    user = premium_data_fixture.create_user(has_active_premium_license=True)
    alternative_per_group_license_service.restrict_user_premium_to(user, [0])
    with pytest.raises(FeaturesNotAvailableError):
        run_export_over_interesting_test_table(
            premium_data_fixture, storage_mock, {"exporter_type": "xml"}, user=user
        )


def strip_indents_and_newlines(xml):
    return "".join([line.strip() for line in xml.split("\n")])


def run_export_over_interesting_test_table(
    premium_data_fixture, storage_mock, options, user_kwargs=None, user=None
):
    table, user, _, _, context = setup_interesting_test_table(
        premium_data_fixture, user_kwargs=user_kwargs, user=user
    )
    grid_view = premium_data_fixture.create_grid_view(table=table)
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
