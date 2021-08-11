import pytest
from pytz import timezone
from datetime import datetime
from freezegun import freeze_time
from io import BytesIO
from django.core.exceptions import ValidationError

from baserow.core.handler import CoreHandler
from baserow.contrib.database.fields.models import CreatedOnField
from baserow.contrib.database.fields.handler import FieldHandler
from baserow.contrib.database.rows.handler import RowHandler


@pytest.mark.django_db
def test_created_on_field_type(data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)

    field_handler = FieldHandler()
    row_handler = RowHandler()
    timezone_to_test = "Europe/Berlin"
    timezone_of_field = timezone(timezone_to_test)
    time_to_freeze = "2021-08-10 12:00"

    data_fixture.create_text_field(table=table, name="text_field", primary=True)
    created_on_field_date = field_handler.create_field(
        user=user,
        table=table,
        type_name="created_on",
        name="Create Date",
        timezone=timezone_to_test,
    )
    created_on_field_datetime = field_handler.create_field(
        user=user,
        table=table,
        type_name="created_on",
        name="Create Datetime",
        date_include_time=True,
        timezone=timezone_to_test,
    )
    assert created_on_field_date.date_include_time is False
    assert created_on_field_datetime.date_include_time is True
    assert len(CreatedOnField.objects.all()) == 2

    model = table.get_model(attribute_names=True)

    with pytest.raises(ValidationError):
        row_handler.create_row(
            user=user, table=table, values={created_on_field_date.id: "2021-08-09"}
        )

    with pytest.raises(ValidationError):
        row_handler.create_row(
            user=user,
            table=table,
            values={created_on_field_datetime.id: "2021-08-09T14:14:33.574356Z"},
        )

    with freeze_time(time_to_freeze):
        row = row_handler.create_row(user=user, table=table, values={}, model=model)
    assert row.create_date is not None
    assert row.create_date == row.created_on

    assert row.create_date is not None
    row_create_datetime = row.create_datetime
    row_created_on = row.created_on
    assert row_create_datetime == row_created_on

    # Trying to update the the created_on field will raise error
    with pytest.raises(ValidationError):
        row_handler.update_row(
            user=user,
            row_id=row.id,
            table=table,
            values={created_on_field_date.id: "2021-08-09"},
        )

    with pytest.raises(ValidationError):
        row_handler.update_row(
            user=user,
            table=table,
            row_id=row.id,
            values={created_on_field_datetime.id: "2021-08-09T14:14:33.574356Z"},
        )

    # Updating the text field will NOT updated
    # the created_on field.
    row_create_datetime_before_update = row.create_datetime
    row_create_date_before_update = row.create_date
    row_handler.update_row(
        user=user,
        table=table,
        row_id=row.id,
        values={
            "text_field": "Hello Test",
        },
        model=model,
    )

    row.refresh_from_db()
    assert row.create_datetime == row_create_datetime_before_update
    assert row.create_date == row_create_date_before_update

    row_create_datetime_before_alter = row.create_datetime

    # changing the field from CreatedOn to Datetime should persist the date
    # in the corresponding timezone
    with freeze_time(time_to_freeze):
        field_handler.update_field(
            user=user,
            field=created_on_field_datetime,
            new_type_name="date",
            date_include_time=True,
        )

    assert len(CreatedOnField.objects.all()) == 1
    row.refresh_from_db()
    field_before_with_timezone = row_create_datetime_before_alter.astimezone(
        timezone_of_field
    )
    assert row.create_datetime.year == field_before_with_timezone.year
    assert row.create_datetime.month == field_before_with_timezone.month
    assert row.create_datetime.day == field_before_with_timezone.day
    assert row.create_datetime.hour == field_before_with_timezone.hour
    assert row.create_datetime.minute == field_before_with_timezone.minute
    assert row.create_datetime.second == field_before_with_timezone.second

    # changing the field from LastModified with Datetime to Text Field should persist
    # the datetime as string
    field_handler.update_field(
        user=user,
        field=created_on_field_datetime,
        new_type_name="created_on",
        date_include_time=True,
        timezone="Europe/Berlin",
    )
    assert len(CreatedOnField.objects.all()) == 2

    row.refresh_from_db()
    row_create_datetime_before_alter = row.create_datetime
    field_handler.update_field(
        user=user,
        field=created_on_field_datetime,
        new_type_name="text",
    )
    row.refresh_from_db()
    assert len(CreatedOnField.objects.all()) == 1
    assert row.create_datetime == row_create_datetime_before_alter.astimezone(
        timezone_of_field
    ).strftime("%d/%m/%Y %H:%M")

    # deleting the fields
    field_handler.delete_field(user=user, field=created_on_field_date)

    assert len(CreatedOnField.objects.all()) == 0


@pytest.mark.django_db
def test_created_on_field_type_wrong_timezone(data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)

    field_handler = FieldHandler()

    with pytest.raises(ValueError):
        field_handler.create_field(
            user=user,
            table=table,
            type_name="created_on",
            name="Create Date",
            timezone="SDj",
        )


@pytest.mark.django_db
def test_import_export_last_modified_field(data_fixture):
    user = data_fixture.create_user()
    imported_group = data_fixture.create_group(user=user)
    database = data_fixture.create_database_application(user=user, name="Placeholder")
    table = data_fixture.create_database_table(name="Example", database=database)
    field_handler = FieldHandler()
    created_on_field = field_handler.create_field(
        user=user,
        table=table,
        name="Created On",
        type_name="created_on",
    )

    row_handler = RowHandler()

    with freeze_time("2020-01-01 12:00"):
        row = row_handler.create_row(
            user=user,
            table=table,
            values={},
        )

    assert getattr(row, f"field_{created_on_field.id}") == datetime(
        2020, 1, 1, 12, 00, tzinfo=timezone("UTC")
    )

    core_handler = CoreHandler()
    exported_applications = core_handler.export_group_applications(
        database.group, BytesIO()
    )

    with freeze_time("2020-01-02 12:00"):
        imported_applications, id_mapping = core_handler.import_applications_to_group(
            imported_group, exported_applications, BytesIO(), None
        )

    imported_database = imported_applications[0]
    imported_tables = imported_database.table_set.all()
    imported_table = imported_tables[0]
    import_created_on_field = imported_table.field_set.all().first().specific

    imported_row = row_handler.get_row(user=user, table=imported_table, row_id=row.id)
    assert imported_row.id == row.id
    assert getattr(imported_row, f"field_{import_created_on_field.id}") == datetime(
        2020, 1, 2, 12, 00, tzinfo=timezone("UTC")
    )
