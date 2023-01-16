from io import BytesIO
from unittest.mock import patch

from django.test.utils import override_settings

import pytest

from baserow.contrib.database.export.handler import ExportHandler
from baserow.core.action.registries import action_type_registry
from baserow.core.jobs.constants import JOB_FINISHED
from baserow.core.jobs.handler import JobHandler
from baserow_enterprise.audit_log.job_types import AuditLogExportJobType
from baserow_enterprise.audit_log.models import AuditLogEntry


@pytest.mark.django_db(transaction=True)
@override_settings(DEBUG=True)
@patch("baserow.contrib.database.export.handler.default_storage")
def test_audit_log_entries_can_be_filtered(
    storage_mock, api_client, enterprise_data_fixture, synced_roles
):

    enterprise_data_fixture.enable_enterprise()

    count = 10
    users = []
    groups = []
    actions = []
    action_types = []

    # insert count * len(action_types) entries
    for _ in range(count):
        user = enterprise_data_fixture.create_user()
        group = enterprise_data_fixture.create_group(user=user)
        actions = enterprise_data_fixture.submit_actions_via_api(
            api_client, user=user, group=group
        )

        users.append(user)
        groups.append(group)
        if not action_types:
            action_types = [a["action_type"].type for a in actions]

    admin_user, _ = enterprise_data_fixture.create_enterprise_admin_user_and_token()

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
        admin_user, AuditLogExportJobType.type, **csv_settings
    )
    csv_export_job.refresh_from_db()
    assert csv_export_job.state == JOB_FINISHED

    data = stub_file.getvalue().decode(csv_settings["export_charset"])
    bom = "\ufeff"

    def render_csv_entry(entry, separator=","):
        action_type = action_type_registry.get(entry.action_type)
        entry_description = action_type.get_long_description(entry.params).replace(
            '"', '""'
        )
        return separator.join(
            [
                entry.user_email,
                f"{entry.user_id}",
                entry.group_name,
                f"{entry.group_id}",
                action_type.get_short_description(),
                f'"{entry_description}"',
                f"{entry.action_timestamp}",
                entry.ip_address,
            ]
        )

    assert data == (
        bom
        + "User Email,User ID,Group Name,Group ID,Action Type,Description,Timestamp,IP Address\r\n"
        + "\r\n".join(render_csv_entry(entry) for entry in AuditLogEntry.objects.all())
        + "\r\n"
    )

    close()

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
        admin_user, AuditLogExportJobType.type, **csv_settings
    )
    csv_export_job.refresh_from_db()
    assert csv_export_job.state == JOB_FINISHED

    data = stub_file.getvalue().decode(csv_settings["export_charset"])
    bom = "\ufeff"

    assert data == (
        bom
        + "\r\n".join(
            render_csv_entry(entry, separator="|")
            for entry in AuditLogEntry.objects.all()
        )
        + "\r\n"
    )

    close()

    # ensure the clean_job method will delete the file
    assert csv_export_job.exported_file_name is not None

    with patch("django.core.files.storage.default_storage.delete") as remove_mock:
        AuditLogExportJobType().before_delete(csv_export_job)
        remove_mock.assert_called_once_with(
            ExportHandler.export_file_path(csv_export_job.exported_file_name)
        )
