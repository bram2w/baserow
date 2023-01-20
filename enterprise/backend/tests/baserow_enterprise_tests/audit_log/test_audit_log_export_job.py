from datetime import datetime
from io import BytesIO
from unittest.mock import patch

from django.test.utils import override_settings
from django.utils.timezone import make_aware

import pytest
from freezegun import freeze_time

from baserow.contrib.database.export.handler import ExportHandler
from baserow.core.actions import CreateGroupActionType
from baserow.core.jobs.constants import JOB_FINISHED
from baserow.core.jobs.handler import JobHandler
from baserow_enterprise.audit_log.job_types import AuditLogExportJobType


@pytest.mark.django_db
@override_settings(DEBUG=True)
@patch("baserow.contrib.database.export.handler.default_storage")
def test_audit_log_export_csv_correctly(
    storage_mock, enterprise_data_fixture, synced_roles
):

    user, _ = enterprise_data_fixture.create_enterprise_admin_user_and_token()

    with freeze_time("2023-01-01 12:00:00"):
        group_1 = CreateGroupActionType.do(user, "group 1").group

    with freeze_time("2023-01-01 12:00:10"):
        group_2 = CreateGroupActionType.do(user, "group 2").group

    csv_settings = {
        "csv_column_separator": ",",
        "csv_first_row_header": True,
        "export_charset": "utf-8",
    }

    stub_file = BytesIO()
    storage_mock.open.return_value = stub_file
    close = stub_file.close
    stub_file.close = lambda: None

    csv_export_job = JobHandler().create_and_start_job(
        user, AuditLogExportJobType.type, **csv_settings, sync=True
    )
    csv_export_job.refresh_from_db()
    assert csv_export_job.state == JOB_FINISHED

    data = stub_file.getvalue().decode(csv_settings["export_charset"])
    bom = "\ufeff"

    assert data == (
        bom
        + "User Email,User ID,Group Name,Group ID,Action Type,Description,Timestamp,IP Address\r\n"
        + f'{user.email},{user.id},{group_2.name},{group_2.id},Create group,"Group ""{group_2.name}"" ({group_2.id}) created.",2023-01-01 12:00:10+00:00,\r\n'
        + f'{user.email},{user.id},{group_1.name},{group_1.id},Create group,"Group ""{group_1.name}"" ({group_1.id}) created.",2023-01-01 12:00:00+00:00,\r\n'
    )

    close()

    # With a different separator and wihout header
    csv_settings = {
        "csv_column_separator": "|",
        "csv_first_row_header": False,
        "export_charset": "utf-8",
    }

    stub_file = BytesIO()
    storage_mock.open.return_value = stub_file
    close = stub_file.close
    stub_file.close = lambda: None

    csv_export_job = JobHandler().create_and_start_job(
        user, AuditLogExportJobType.type, **csv_settings, sync=True
    )
    csv_export_job.refresh_from_db()
    assert csv_export_job.state == JOB_FINISHED

    data = stub_file.getvalue().decode(csv_settings["export_charset"])
    bom = "\ufeff"

    assert data == (
        bom
        + f'{user.email}|{user.id}|{group_2.name}|{group_2.id}|Create group|"Group ""{group_2.name}"" ({group_2.id}) created."|2023-01-01 12:00:10+00:00|\r\n'
        + f'{user.email}|{user.id}|{group_1.name}|{group_1.id}|Create group|"Group ""{group_1.name}"" ({group_1.id}) created."|2023-01-01 12:00:00+00:00|\r\n'
    )

    close()


@pytest.mark.django_db
@patch("baserow.contrib.database.export.handler.default_storage")
@override_settings(DEBUG=True)
def test_audit_log_export_csv_in_the_user_language(
    storage_mock, enterprise_data_fixture, synced_roles
):

    user, _ = enterprise_data_fixture.create_enterprise_admin_user_and_token(
        language="it"
    )

    with freeze_time("2023-01-01 12:00:00"):
        group_1 = CreateGroupActionType.do(user, "group 1").group

    csv_settings = {
        "csv_column_separator": ",",
        "csv_first_row_header": False,
        "export_charset": "utf-8",
    }

    stub_file = BytesIO()
    storage_mock.open.return_value = stub_file
    close = stub_file.close
    stub_file.close = lambda: None

    csv_export_job = JobHandler().create_and_start_job(
        user, AuditLogExportJobType.type, **csv_settings, sync=True
    )
    csv_export_job.refresh_from_db()
    assert csv_export_job.state == JOB_FINISHED

    data = stub_file.getvalue().decode(csv_settings["export_charset"])
    bom = "\ufeff"

    assert data == (
        bom
        + f'{user.email},{user.id},{group_1.name},{group_1.id},Crea gruppo,"Gruppo ""{group_1.name}"" ({group_1.id}) creato.",2023-01-01 12:00:00+00:00,\r\n'
    )

    close()


@pytest.mark.django_db
@patch("baserow.contrib.database.export.handler.default_storage")
@override_settings(DEBUG=True)
def test_deleting_audit_log_export_job_also_delete_exported_file(
    storage_mock, enterprise_data_fixture, synced_roles
):

    user, _ = enterprise_data_fixture.create_enterprise_admin_user_and_token()
    csv_settings = {
        "csv_column_separator": ",",
        "csv_first_row_header": True,
        "export_charset": "utf-8",
    }
    stub_file = BytesIO()
    storage_mock.open.return_value = stub_file
    close = stub_file.close
    stub_file.close = lambda: None

    csv_export_job = JobHandler().create_and_start_job(
        user, AuditLogExportJobType.type, **csv_settings, sync=True
    )
    csv_export_job.refresh_from_db()
    assert csv_export_job.state == JOB_FINISHED

    close()

    # ensure the clean_job method will delete the file
    assert csv_export_job.exported_file_name is not None

    with patch("django.core.files.storage.default_storage.delete") as remove_mock:
        AuditLogExportJobType().before_delete(csv_export_job)
        remove_mock.assert_called_once_with(
            ExportHandler.export_file_path(csv_export_job.exported_file_name)
        )


@pytest.mark.django_db
@patch("baserow.contrib.database.export.handler.default_storage")
@override_settings(DEBUG=True)
def test_audit_log_export_filters_work_correctly(
    storage_mock, enterprise_data_fixture, synced_roles
):

    user, _ = enterprise_data_fixture.create_enterprise_admin_user_and_token()

    with freeze_time("2023-01-01 12:00:00"):
        group_1 = CreateGroupActionType.do(user, "group 1").group

    with freeze_time("2023-01-01 12:00:10"):
        group_2 = CreateGroupActionType.do(user, "group 2").group

    csv_settings = {
        "csv_column_separator": ",",
        "csv_first_row_header": True,
        "export_charset": "utf-8",
    }

    job = JobHandler().create_and_start_job(
        user, AuditLogExportJobType.type, **csv_settings, sync=True
    )
    job.refresh_from_db()
    job_type = AuditLogExportJobType()

    assert job_type.get_filtered_queryset(job).count() == 2

    job.filter_user_id = user.id + 1
    assert job_type.get_filtered_queryset(job).count() == 0
    job.filter_user_id = None

    job.filter_group_id = group_1.id
    assert job_type.get_filtered_queryset(job).count() == 1
    job.filter_group_id = None

    job.filter_action_type = "delete_group"
    assert job_type.get_filtered_queryset(job).count() == 0
    job.filter_action_type = None

    job.filter_from_timestamp = make_aware(
        datetime.strptime("2023-01-01 12:00:05", "%Y-%m-%d %H:%M:%S")
    )
    assert job_type.get_filtered_queryset(job).count() == 1

    job.filter_to_timestamp = make_aware(
        datetime.strptime("2023-01-01 12:00:08", "%Y-%m-%d %H:%M:%S")
    )
    assert job_type.get_filtered_queryset(job).count() == 0
