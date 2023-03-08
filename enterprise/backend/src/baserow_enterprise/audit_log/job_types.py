from collections import OrderedDict
from typing import Dict
from uuid import uuid4

from django.core.files.storage import default_storage
from django.core.paginator import Paginator
from django.utils.functional import lazy
from django.utils.translation import gettext as _
from django.utils.translation import override as translation_override

import unicodecsv as csv
from baserow_premium.license.handler import LicenseHandler
from loguru import logger
from rest_framework import serializers

from baserow.contrib.database.api.export.serializers import (
    SUPPORTED_CSV_COLUMN_SEPARATORS,
    SUPPORTED_EXPORT_CHARSETS,
    DisplayChoiceField,
    ExportedFileURLSerializerMixin,
)
from baserow.contrib.database.export.handler import (
    ExportHandler,
    _create_storage_dir_if_missing_and_open,
)
from baserow.core.action.registries import action_type_registry
from baserow.core.jobs.registries import JobType
from baserow.core.utils import ChildProgressBuilder
from baserow_enterprise.features import AUDIT_LOG

from .models import AuditLogEntry, AuditLogExportJob


class AuditLogExportJobType(JobType):
    type = "audit_log_export"
    model_class = AuditLogExportJob
    max_count = 1

    serializer_mixins = [ExportedFileURLSerializerMixin]
    request_serializer_field_names = [
        "csv_column_separator",
        "csv_first_row_header",
        "export_charset",
        "filter_user_id",
        "filter_group_id",
        "filter_action_type",
        "filter_from_timestamp",
        "filter_to_timestamp",
    ]

    serializer_field_names = [
        "csv_column_separator",
        "csv_first_row_header",
        "export_charset",
        "filter_user_id",
        "filter_group_id",
        "filter_action_type",
        "filter_from_timestamp",
        "filter_to_timestamp",
        "created_on",
        "exported_file_name",
        "url",
    ]
    serializer_field_overrides = {
        # Map to the python encoding aliases at the same time by using a
        # DisplayChoiceField
        "export_charset": DisplayChoiceField(
            choices=SUPPORTED_EXPORT_CHARSETS,
            default="utf-8",
            help_text="The character set to use when creating the export file.",
        ),
        # For ease of use we expect the JSON to contain human typeable forms of each
        # different separator instead of the unicode character itself. By using the
        # DisplayChoiceField we can then map this to the actual separator character by
        # having those be the second value of each choice tuple.
        "csv_column_separator": DisplayChoiceField(
            choices=SUPPORTED_CSV_COLUMN_SEPARATORS,
            default=",",
            help_text="The value used to separate columns in the resulting csv file.",
        ),
        "csv_first_row_header": serializers.BooleanField(
            default=True,
            help_text="Whether or not to generate a header row at the top of the csv file.",
        ),
        "filter_user_id": serializers.IntegerField(
            min_value=0,
            required=False,
            help_text="Optional: The user to filter the audit log by.",
        ),
        "filter_group_id": serializers.IntegerField(
            min_value=0,
            required=False,
            help_text="Optional: The group to filter the audit log by.",
        ),
        "filter_action_type": serializers.ChoiceField(
            choices=lazy(action_type_registry.get_types, list)(),
            required=False,
            default=None,
            help_text="Optional: The action type to filter the audit log by.",
        ),
        "filter_from_timestamp": serializers.DateTimeField(
            required=False,
            help_text="Optional: The start date to filter the audit log by.",
        ),
        "filter_to_timestamp": serializers.DateTimeField(
            required=False,
            help_text="Optional: The end date to filter the audit log by.",
        ),
        "created_on": serializers.DateTimeField(
            read_only=True,
            help_text="The date and time when the export job was created.",
        ),
    }

    def before_delete(self, job):
        """
        Try to delete the data file of a job before deleting the job.
        """

        if not job.exported_file_name:
            return

        storage_location = ExportHandler.export_file_path(job.exported_file_name)
        try:
            default_storage.delete(storage_location)
        except FileNotFoundError:
            logger.error(
                "Could not delete file %s for 'audit_log_export' job %s",
                storage_location,
                job.id,
            )

    def write_audit_log_rows(self, job, file, queryset, progress):

        # add BOM to support utf-8 CSVs in MS Excel (for Windows only)
        if job.export_charset == "utf-8":
            file.write(b"\xef\xbb\xbf")

        field_header_mapping = OrderedDict(
            {
                "user_email": _("User Email"),
                "user_id": _("User ID"),
                "group_name": _("Group Name"),
                "group_id": _("Group ID"),
                "type": _("Action Type"),
                "description": _("Description"),
                "action_timestamp": _("Timestamp"),
                "ip_address": _("IP Address"),
            }
        )

        writer = csv.writer(
            file,
            field_header_mapping.values(),
            encoding=job.export_charset,
            delimiter=job.csv_column_separator,
        )

        if job.csv_first_row_header:
            writer.writerow(field_header_mapping.values())

        fields = field_header_mapping.keys()
        paginator = Paginator(queryset.all(), 2000)
        export_progress = ChildProgressBuilder.build(
            progress.create_child_builder(represents_progress=progress.total),
            paginator.num_pages,
        )

        for page in paginator.page_range:
            rows = [
                [getattr(row, field) for field in fields]
                for row in paginator.page(page).object_list
            ]
            writer.writerows(rows)
            export_progress.increment()

    def get_filtered_queryset(self, job):
        queryset = AuditLogEntry.objects.order_by("-action_timestamp")
        filters_field_mapping: Dict[str, str] = {
            "filter_user_id": "user_id",
            "filter_group_id": "group_id",
            "filter_action_type": "action_type",
            "filter_from_timestamp": "action_timestamp__gte",
            "filter_to_timestamp": "action_timestamp__lte",
        }

        for field, qs_filter in filters_field_mapping.items():
            if (value := getattr(job, field)) is not None:
                queryset = queryset.filter(**{qs_filter: value})

        return queryset

    def run(self, job, progress):
        """
        Export the filtered audit log entries to a CSV file.

        :param job: The job that is currently being executed.
        :progress: The progress object that can be used to update the progress bar.
        """

        LicenseHandler.raise_if_user_doesnt_have_feature_instance_wide(
            AUDIT_LOG, job.user
        )

        queryset = self.get_filtered_queryset(job)

        filename = f"{uuid4()}.csv"
        storage_location = ExportHandler.export_file_path(filename)
        with _create_storage_dir_if_missing_and_open(storage_location) as file:
            with translation_override(job.user.profile.language):
                self.write_audit_log_rows(job, file, queryset, progress)

        job.exported_file_name = filename
        job.save()
