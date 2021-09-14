from unittest.mock import patch

import pytest
from django.core.files.storage import FileSystemStorage
from django.urls import reverse
from django.utils.dateparse import parse_datetime
from django.utils.timezone import utc, make_aware
from freezegun import freeze_time
from rest_framework.fields import DateTimeField
from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND, HTTP_200_OK

from baserow.contrib.database.rows.handler import RowHandler


@pytest.mark.django_db
def test_unknown_export_type_for_table_returns_error(data_fixture, api_client, tmpdir):
    user, token = data_fixture.create_user_and_token()
    table = data_fixture.create_database_table(user=user)
    data_fixture.create_text_field(table=table, name="text_field")

    response = api_client.post(
        reverse(
            "api:database:export:export_table",
            kwargs={"table_id": table.id},
        ),
        data={
            "exporter_type": "unknown",
            "export_charset": "utf-8",
            "csv_include_header": "True",
            "csv_column_separator": ",",
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_REQUEST_BODY_VALIDATION"


@pytest.mark.django_db
def test_exporting_table_without_permissions_returns_error(
    data_fixture, api_client, tmpdir
):
    user = data_fixture.create_user()
    unpermissioned_user, unpermissioned_token = data_fixture.create_user_and_token()
    table = data_fixture.create_database_table(user=user)
    data_fixture.create_text_field(table=table, name="text_field")

    response = api_client.post(
        reverse(
            "api:database:export:export_table",
            kwargs={"table_id": table.id},
        ),
        data={
            "exporter_type": "csv",
            "export_charset": "utf-8",
            "csv_include_header": "True",
            "csv_column_separator": ",",
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {unpermissioned_token}",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_USER_NOT_IN_GROUP"


@pytest.mark.django_db
def test_exporting_missing_view_returns_error(data_fixture, api_client, tmpdir):
    user, token = data_fixture.create_user_and_token()
    table = data_fixture.create_database_table(user=user)
    response = api_client.post(
        reverse(
            "api:database:export:export_table",
            kwargs={"table_id": table.id},
        ),
        data={
            "view_id": 9999,
            "exporter_type": "csv",
            "export_charset": "utf-8",
            "csv_include_header": "True",
            "csv_column_separator": ",",
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_VIEW_DOES_NOT_EXIST"


@pytest.mark.django_db
def test_exporting_view_which_isnt_for_table_returns_error(
    data_fixture, api_client, tmpdir
):
    user, token = data_fixture.create_user_and_token()
    table = data_fixture.create_database_table(user=user)
    grid_view_for_other_table = data_fixture.create_grid_view()
    response = api_client.post(
        reverse(
            "api:database:export:export_table",
            kwargs={"table_id": table.id},
        ),
        data={
            "view_id": grid_view_for_other_table.id,
            "exporter_type": "csv",
            "export_charset": "utf-8",
            "csv_include_header": "True",
            "csv_column_separator": ",",
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_VIEW_NOT_IN_TABLE"


@pytest.mark.django_db
def test_exporting_missing_table_returns_error(data_fixture, api_client, tmpdir):
    user, token = data_fixture.create_user_and_token()
    response = api_client.post(
        reverse(
            "api:database:export:export_table",
            kwargs={"table_id": 9999},
        ),
        data={
            "exporter_type": "csv",
            "export_charset": "utf-8",
            "csv_include_header": "True",
            "csv_column_separator": ",",
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_TABLE_DOES_NOT_EXIST"


@pytest.mark.django_db
def test_getting_missing_export_job_returns_error(data_fixture, api_client, tmpdir):
    user, token = data_fixture.create_user_and_token()
    response = api_client.get(
        reverse("api:database:export:get", kwargs={"job_id": 9999}),
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_EXPORT_JOB_DOES_NOT_EXIST"


@pytest.mark.django_db
def test_getting_other_users_export_job_returns_error(data_fixture, api_client, tmpdir):
    user, token = data_fixture.create_user_and_token()
    unpermissioned_user, unpermissioned_token = data_fixture.create_user_and_token()
    table = data_fixture.create_database_table(user=user)
    data_fixture.create_text_field(table=table, name="text_field")
    response = api_client.post(
        reverse(
            "api:database:export:export_table",
            kwargs={"table_id": table.id},
        ),
        data={
            "exporter_type": "csv",
            "export_charset": "utf-8",
            "csv_include_header": "True",
            "csv_column_separator": ",",
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_200_OK

    response = api_client.get(
        reverse("api:database:export:get", kwargs={"job_id": 9999}),
        format="json",
        HTTP_AUTHORIZATION=f"JWT {unpermissioned_token}",
    )
    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_EXPORT_JOB_DOES_NOT_EXIST"


@pytest.mark.django_db
def test_exporting_csv_writes_file_to_storage(
    data_fixture, api_client, tmpdir, settings, django_capture_on_commit_callbacks
):
    user, token = data_fixture.create_user_and_token()
    table = data_fixture.create_database_table(user=user)
    text_field = data_fixture.create_text_field(table=table, name="text_field", order=0)
    option_field = data_fixture.create_single_select_field(
        table=table, name="option_field", order=1
    )
    option_a = data_fixture.create_select_option(
        field=option_field, value="A", color="blue"
    )
    option_b = data_fixture.create_select_option(
        field=option_field, value="B", color="red"
    )
    date_field = data_fixture.create_date_field(
        table=table,
        date_include_time=True,
        date_format="US",
        name="date_field",
        order=2,
    )

    grid_view = data_fixture.create_grid_view(table=table)
    data_fixture.create_view_filter(
        view=grid_view, field=text_field, type="contains", value="test"
    )
    data_fixture.create_view_sort(view=grid_view, field=text_field, order="ASC")

    row_handler = RowHandler()
    row_handler.create_row(
        user=user,
        table=table,
        values={
            text_field.id: "test",
            date_field.id: "2020-02-01 01:23",
            option_field.id: option_b.id,
        },
    )
    row_handler.create_row(
        user=user,
        table=table,
        values={
            text_field.id: "atest",
            date_field.id: "2020-02-01 01:23",
            option_field.id: option_a.id,
        },
    )
    storage = FileSystemStorage(location=(str(tmpdir)), base_url="http://localhost")

    with patch("baserow.contrib.database.export.handler.default_storage", new=storage):
        run_time = make_aware(parse_datetime("2020-02-01 01:00"), timezone=utc)
        # DRF uses some custom internal date time formatting, use the field itself
        # so the test doesn't break if we set a different default timezone format etc
        expected_created_at = DateTimeField().to_representation(run_time)
        with freeze_time(run_time):
            with django_capture_on_commit_callbacks(execute=True):
                response = api_client.post(
                    reverse(
                        "api:database:export:export_table",
                        kwargs={"table_id": table.id},
                    ),
                    data={
                        "view_id": grid_view.id,
                        "exporter_type": "csv",
                        "export_charset": "utf-8",
                        "csv_include_header": "True",
                        "csv_column_separator": ",",
                    },
                    format="json",
                    HTTP_AUTHORIZATION=f"JWT {token}",
                )
            response_json = response.json()
            job_id = response_json["id"]
            assert response_json == {
                "id": job_id,
                "created_at": expected_created_at,
                "exported_file_name": None,
                "exporter_type": "csv",
                "progress_percentage": 0.0,
                "status": "pending",
                "table": table.id,
                "view": grid_view.id,
                "url": None,
            }
            response = api_client.get(
                reverse("api:database:export:get", kwargs={"job_id": job_id}),
                format="json",
                HTTP_AUTHORIZATION=f"JWT {token}",
            )
            json = response.json()
            filename = json["exported_file_name"]
            assert json == {
                "id": job_id,
                "created_at": expected_created_at,
                "exported_file_name": filename,
                "exporter_type": "csv",
                "progress_percentage": 1.0,
                "status": "complete",
                "table": table.id,
                "view": grid_view.id,
                "url": f"http://localhost:8000/media/export_files/{filename}",
            }

            file_path = tmpdir.join(settings.EXPORT_FILES_DIRECTORY, filename)
            assert file_path.isfile()
            expected = (
                "\ufeff"
                "id,text_field,option_field,date_field\n"
                "2,atest,A,02/01/2020 01:23\n"
                "1,test,B,02/01/2020 01:23\n"
            )
            with open(file_path, "r", encoding="utf-8") as written_file:
                assert written_file.read() == expected


@pytest.mark.django_db
def test_exporting_csv_table_writes_file_to_storage(
    data_fixture, api_client, tmpdir, settings, django_capture_on_commit_callbacks
):
    user, token = data_fixture.create_user_and_token()
    table = data_fixture.create_database_table(user=user)
    text_field = data_fixture.create_text_field(table=table, name="text_field", order=0)
    option_field = data_fixture.create_single_select_field(
        table=table, name="option_field", order=1
    )
    option_a = data_fixture.create_select_option(
        field=option_field, value="A", color="blue"
    )
    option_b = data_fixture.create_select_option(
        field=option_field, value="B", color="red"
    )
    date_field = data_fixture.create_date_field(
        table=table,
        date_include_time=True,
        date_format="US",
        name="date_field",
        order=2,
    )

    grid_view = data_fixture.create_grid_view(table=table)
    data_fixture.create_view_filter(
        view=grid_view, field=text_field, type="contains", value="test"
    )
    data_fixture.create_view_sort(view=grid_view, field=text_field, order="ASC")

    row_handler = RowHandler()
    row_handler.create_row(
        user=user,
        table=table,
        values={
            text_field.id: "test",
            date_field.id: "2020-02-01 01:23",
            option_field.id: option_b.id,
        },
    )
    row_handler.create_row(
        user=user,
        table=table,
        values={
            text_field.id: "atest",
            date_field.id: "2020-02-01 01:23",
            option_field.id: option_a.id,
        },
    )
    storage = FileSystemStorage(location=(str(tmpdir)), base_url="http://localhost")

    with patch("baserow.contrib.database.export.handler.default_storage", new=storage):
        run_time = make_aware(parse_datetime("2020-02-01 01:00"), timezone=utc)
        # DRF uses some custom internal date time formatting, use the field itself
        # so the test doesn't break if we set a different default timezone format etc
        expected_created_at = DateTimeField().to_representation(run_time)
        with freeze_time(run_time):
            with django_capture_on_commit_callbacks(execute=True):
                response = api_client.post(
                    reverse(
                        "api:database:export:export_table",
                        kwargs={"table_id": table.id},
                    ),
                    data={
                        "view_id": None,
                        "exporter_type": "csv",
                        "export_charset": "utf-8",
                        "csv_include_header": "True",
                        "csv_column_separator": ",",
                    },
                    format="json",
                    HTTP_AUTHORIZATION=f"JWT {token}",
                )
            response_json = response.json()
            job_id = response_json["id"]
            assert response_json == {
                "id": job_id,
                "created_at": expected_created_at,
                "exported_file_name": None,
                "exporter_type": "csv",
                "progress_percentage": 0.0,
                "status": "pending",
                "table": table.id,
                "view": None,
                "url": None,
            }
            response = api_client.get(
                reverse("api:database:export:get", kwargs={"job_id": job_id}),
                format="json",
                HTTP_AUTHORIZATION=f"JWT {token}",
            )
            json = response.json()
            filename = json["exported_file_name"]
            assert json == {
                "id": job_id,
                "created_at": expected_created_at,
                "exported_file_name": filename,
                "exporter_type": "csv",
                "progress_percentage": 1.0,
                "status": "complete",
                "table": table.id,
                "view": None,
                "url": f"http://localhost:8000/media/export_files/{filename}",
            }

            file_path = tmpdir.join(settings.EXPORT_FILES_DIRECTORY, filename)
            assert file_path.isfile()
            expected = (
                "\ufeff"
                "id,text_field,option_field,date_field\n"
                "1,test,B,02/01/2020 01:23\n"
                "2,atest,A,02/01/2020 01:23\n"
            )
            with open(file_path, "r", encoding="utf-8") as written_file:
                assert written_file.read() == expected
