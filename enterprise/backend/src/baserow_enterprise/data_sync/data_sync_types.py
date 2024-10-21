from datetime import date, datetime
from typing import Any, Dict, List
from uuid import UUID

import advocate
from advocate import UnacceptableAddressException
from baserow_premium.fields.field_types import AIFieldType
from baserow_premium.license.handler import LicenseHandler
from jira2markdown import convert
from requests.auth import HTTPBasicAuth
from requests.exceptions import JSONDecodeError, RequestException
from rest_framework import serializers

from baserow.contrib.database.data_sync.data_sync_types import compare_date
from baserow.contrib.database.data_sync.exceptions import SyncError
from baserow.contrib.database.data_sync.models import DataSyncSyncedProperty
from baserow.contrib.database.data_sync.registries import DataSyncProperty, DataSyncType
from baserow.contrib.database.fields.field_types import (
    AutonumberFieldType,
    BooleanFieldType,
    CreatedOnFieldType,
    DateFieldType,
    DurationFieldType,
    EmailFieldType,
    FileFieldType,
    LastModifiedFieldType,
    LongTextFieldType,
    NumberFieldType,
    PhoneNumberFieldType,
    RatingFieldType,
    TextFieldType,
    URLFieldType,
    UUIDFieldType,
)
from baserow.contrib.database.fields.models import (
    DateField,
    Field,
    LongTextField,
    NumberField,
    TextField,
    URLField,
)
from baserow.contrib.database.fields.registries import field_type_registry
from baserow.contrib.database.rows.operations import ReadDatabaseRowOperationType
from baserow.contrib.database.table.exceptions import TableDoesNotExist
from baserow.contrib.database.table.handler import TableHandler
from baserow.core.db import specific_iterator
from baserow.core.handler import CoreHandler
from baserow.core.utils import get_value_at_path
from baserow_enterprise.features import DATA_SYNC

from .models import JiraIssuesDataSync, LocalBaserowTableDataSync


class RowIDDataSyncProperty(DataSyncProperty):
    unique_primary = True
    immutable_properties = True

    def to_baserow_field(self) -> NumberField:
        return NumberField(
            name=self.name, number_decimal_places=0, number_negative=False
        )


class BaserowFieldDataSyncProperty(DataSyncProperty):
    supported_field_types = [
        TextFieldType.type,
        LongTextFieldType.type,
        URLFieldType.type,
        EmailFieldType.type,
        NumberFieldType.type,
        RatingFieldType.type,
        BooleanFieldType.type,
        DateFieldType.type,
        DurationFieldType.type,
        FileFieldType.type,
        PhoneNumberFieldType.type,
        CreatedOnFieldType.type,
        LastModifiedFieldType.type,
        UUIDFieldType.type,
        AutonumberFieldType.type,
        AIFieldType.type,
    ]
    field_types_override = {
        CreatedOnFieldType.type: DateField,
        LastModifiedFieldType.type: DateField,
        UUIDFieldType.type: TextField,
        AutonumberFieldType.type: NumberField,
        AIFieldType.type: LongTextField,
    }

    def __init__(self, field, immutable_properties, **kwargs):
        self.field = field
        self.immutable_properties = immutable_properties
        super().__init__(**kwargs)

    def to_baserow_field(self) -> Field:
        field_type = field_type_registry.get_by_model(self.field)
        allowed_fields = ["name"] + field_type.allowed_fields
        model_class = self.field_types_override.get(
            field_type.type, field_type.model_class
        )
        return model_class(
            **{
                allowed_field: getattr(self.field, allowed_field)
                for allowed_field in allowed_fields
                if hasattr(self.field, allowed_field)
                and hasattr(model_class, allowed_field)
            }
        )

    def is_equal(self, baserow_row_value: Any, data_sync_row_value: Any) -> bool:
        # The CreatedOn and LastModified fields are always stored as datetime in the
        # source table, but not always in the data sync table, so if that happens we'll
        # compare loosely.
        if isinstance(baserow_row_value, date) and isinstance(
            data_sync_row_value, datetime
        ):
            return compare_date(baserow_row_value, data_sync_row_value)
        # The baserow row value is converted to a string, so we would need to convert
        # the uuid object to a string to do a good comparison.
        if isinstance(data_sync_row_value, UUID):
            data_sync_row_value = str(data_sync_row_value)
        return super().is_equal(baserow_row_value, data_sync_row_value)


class LocalBaserowTableDataSyncType(DataSyncType):
    type = "local_baserow_table"
    model_class = LocalBaserowTableDataSync
    allowed_fields = ["source_table_id", "authorized_user_id"]
    serializer_field_names = ["source_table_id"]
    serializer_field_overrides = {
        "source_table_id": serializers.IntegerField(
            help_text="The ID of the source table that must be synced.",
            required=True,
            allow_null=False,
        ),
    }

    def prepare_values(self, user, values):
        # The user that creates the data sync is automatically the one on whose
        # behalf the data is synced in the future.
        values["authorized_user_id"] = user.id
        return values

    def prepare_sync_job_values(self, instance):
        # Raise the error so that the job doesn't start and the user is informed with
        # the correct error.
        LicenseHandler.raise_if_workspace_doesnt_have_feature(
            DATA_SYNC, instance.table.database.workspace
        )

    def _get_table(self, instance):
        try:
            table = TableHandler().get_table(instance.source_table_id)
        except TableDoesNotExist:
            raise SyncError("The source table doesn't exist.")

        if not CoreHandler().check_permissions(
            instance.authorized_user,
            ReadDatabaseRowOperationType.type,
            workspace=table.database.workspace,
            context=table,
            raise_permission_exceptions=False,
        ):
            raise SyncError("The authorized user doesn't have access to the table.")

        return table

    def get_properties(self, instance) -> List[DataSyncProperty]:
        table = self._get_table(instance)
        # The `table_id` is not set if when just listing the properties using the
        # `DataSyncPropertiesView` endpoint, but it will be set when creating the view.
        if instance.table_id:
            LicenseHandler.raise_if_workspace_doesnt_have_feature(
                DATA_SYNC, instance.table.database.workspace
            )
        fields = specific_iterator(table.field_set.all())
        properties = [RowIDDataSyncProperty("id", "Row ID")]

        return properties + [
            BaserowFieldDataSyncProperty(
                field=field,
                immutable_properties=True,
                key=f"field_{field.id}",
                name=field.name,
            )
            for field in fields
            if field_type_registry.get_by_model(field).type
            in BaserowFieldDataSyncProperty.supported_field_types
        ]

    def get_all_rows(self, instance) -> List[Dict]:
        table = self._get_table(instance)
        enabled_properties = DataSyncSyncedProperty.objects.filter(data_sync=instance)
        enabled_property_field_ids = [p.key for p in enabled_properties]
        model = table.get_model()
        rows_queryset = model.objects.all().values(*["id"] + enabled_property_field_ids)
        return rows_queryset


class JiraIDDataSyncProperty(DataSyncProperty):
    unique_primary = True
    immutable_properties = True

    def to_baserow_field(self) -> TextField:
        return TextField(name=self.name)


class JiraSummaryDataSyncProperty(DataSyncProperty):
    immutable_properties = True

    def to_baserow_field(self) -> TextField:
        return TextField(name=self.name)


class JiraDescriptionDataSyncProperty(DataSyncProperty):
    immutable_properties = True

    def to_baserow_field(self) -> LongTextField:
        return LongTextField(name=self.name, long_text_enable_rich_text=True)


class JiraAssigneeDataSyncProperty(DataSyncProperty):
    immutable_properties = True

    def to_baserow_field(self) -> TextField:
        return TextField(name=self.name)


class JiraReporterDataSyncProperty(DataSyncProperty):
    immutable_properties = True

    def to_baserow_field(self) -> TextField:
        return TextField(name=self.name)


class JiraLabelsDataSyncProperty(DataSyncProperty):
    immutable_properties = True

    def to_baserow_field(self) -> TextField:
        return TextField(name=self.name)


class JiraCreatedDateDataSyncProperty(DataSyncProperty):
    immutable_properties = True

    def to_baserow_field(self) -> DateField:
        return DateField(
            name=self.name,
            date_format="ISO",
            date_include_time=True,
            date_time_format="24",
            date_show_tzinfo=True,
        )

    def is_equal(self, baserow_row_value: Any, data_sync_row_value: Any) -> bool:
        return compare_date(baserow_row_value, data_sync_row_value)


class JiraUpdatedDateDataSyncProperty(DataSyncProperty):
    immutable_properties = True

    def to_baserow_field(self) -> DateField:
        return DateField(
            name=self.name,
            date_format="ISO",
            date_include_time=True,
            date_time_format="24",
            date_show_tzinfo=True,
        )

    def is_equal(self, baserow_row_value: Any, data_sync_row_value: Any) -> bool:
        return compare_date(baserow_row_value, data_sync_row_value)


class JiraResolvedDateDataSyncProperty(DataSyncProperty):
    immutable_properties = True

    def to_baserow_field(self) -> DateField:
        return DateField(
            name=self.name,
            date_format="ISO",
            date_include_time=True,
            date_time_format="24",
            date_show_tzinfo=True,
        )

    def is_equal(self, baserow_row_value: Any, data_sync_row_value: Any) -> bool:
        return compare_date(baserow_row_value, data_sync_row_value)


class JiraDueDateDataSyncProperty(DataSyncProperty):
    immutable_properties = True

    def to_baserow_field(self) -> DateField:
        return DateField(
            name=self.name,
            date_format="ISO",
            date_include_time=True,
            date_time_format="24",
            date_show_tzinfo=True,
        )

    def is_equal(self, baserow_row_value: Any, data_sync_row_value: Any) -> bool:
        return compare_date(baserow_row_value, data_sync_row_value)


class JiraStateDataSyncProperty(DataSyncProperty):
    immutable_properties = True

    def to_baserow_field(self) -> TextField:
        return TextField(name=self.name)


class JiraProjectDataSyncProperty(DataSyncProperty):
    immutable_properties = True

    def to_baserow_field(self) -> TextField:
        return TextField(name=self.name)


class JiraURLDataSyncProperty(DataSyncProperty):
    immutable_properties = True

    def to_baserow_field(self) -> URLField:
        return URLField(name=self.name)


class JiraIssuesDataSyncType(DataSyncType):
    type = "jira_issues"
    model_class = JiraIssuesDataSync
    allowed_fields = ["jira_url", "jira_project_key", "jira_username", "jira_api_token"]
    serializer_field_names = [
        "jira_url",
        "jira_project_key",
        "jira_username",
        "jira_api_token",
    ]

    def prepare_sync_job_values(self, instance):
        # Raise the error so that the job doesn't start and the user is informed with
        # the correct error.
        LicenseHandler.raise_if_workspace_doesnt_have_feature(
            DATA_SYNC, instance.table.database.workspace
        )

    def get_properties(self, instance) -> List[DataSyncProperty]:
        # The `table_id` is not set if when just listing the properties using the
        # `DataSyncPropertiesView` endpoint, but it will be set when creating the view.
        if instance.table_id:
            LicenseHandler.raise_if_workspace_doesnt_have_feature(
                DATA_SYNC, instance.table.database.workspace
            )
        return [
            JiraIDDataSyncProperty("jira_id", "Jira Issue ID"),
            JiraSummaryDataSyncProperty("summary", "Summary"),
            JiraDescriptionDataSyncProperty("description", "Description"),
            JiraAssigneeDataSyncProperty("assignee", "Assignee"),
            JiraReporterDataSyncProperty("reporter", "Reporter"),
            JiraLabelsDataSyncProperty("labels", "Labels"),
            JiraCreatedDateDataSyncProperty("created", "Created Date"),
            JiraUpdatedDateDataSyncProperty("updated", "Updated Date"),
            JiraResolvedDateDataSyncProperty("resolved", "Resolved Date"),
            JiraDueDateDataSyncProperty("due", "Due Date"),
            JiraStateDataSyncProperty("status", "State"),
            JiraStateDataSyncProperty("project", "Project"),
            JiraURLDataSyncProperty("url", "Issue URL"),
        ]

    def _parse_datetime(self, value):
        if not value:
            return None

        try:
            return datetime.fromisoformat(value)
        except ValueError:
            raise SyncError(f"The date {value} could not be parsed.")

    def _fetch_issues(self, instance):
        headers = {"Content-Type": "application/json"}
        issues = []
        start_at = 0
        max_results = 50
        try:
            while True:
                url = (
                    f"{instance.jira_url}"
                    + f"/rest/api/2/search"
                    + f"?startAt={start_at}"
                    + f"&maxResults={max_results}"
                )
                if instance.jira_project_key:
                    url += f"&jql=project={instance.jira_project_key}"

                response = advocate.get(
                    url,
                    auth=HTTPBasicAuth(instance.jira_username, instance.jira_api_token),
                    headers=headers,
                    timeout=10,
                )
                if not response.ok:
                    try:
                        json = response.json()
                        if "errorMessages" in json and len(json["errorMessages"]) > 0:
                            raise SyncError(json["errorMessages"][0])
                    except JSONDecodeError:
                        pass
                    raise SyncError(
                        "The request to Jira did not return an OK response."
                    )

                data = response.json()

                if len(data["issues"]) == 0 and start_at == 0:
                    raise SyncError(
                        "No issues found. This is usually because the authentication "
                        "details are wrong."
                    )

                issues.extend(data["issues"])
                start_at += max_results
                if data["total"] <= start_at:
                    break
        except (RequestException, UnacceptableAddressException, ConnectionError):
            raise SyncError("Error fetching issues from Jira.")

        return issues

    def get_all_rows(self, instance) -> List[Dict]:
        issue_list = []
        for issue in self._fetch_issues(instance):
            try:
                jira_id = issue["id"]
                issue_url = f"{instance.jira_url}/browse/{issue['key']}"
            except KeyError:
                raise SyncError(
                    "The `id` and `key` are not found in the issue. This is likely the "
                    "result of an invalid response from Jira."
                )
            summary = get_value_at_path(issue, "fields.summary", "")
            description = get_value_at_path(issue, "fields.description", "") or ""
            assignee = get_value_at_path(issue, "fields.assignee.displayName", "")
            reporter = get_value_at_path(issue, "fields.reporter.displayName", "")
            project = get_value_at_path(issue, "fields.project.name", "")
            status = get_value_at_path(issue, "fields.status.name", "")
            labels = ", ".join(issue["fields"].get("labels", []))
            created = self._parse_datetime(issue["fields"].get("created"))
            updated = self._parse_datetime(issue["fields"].get("updated"))
            resolved = self._parse_datetime(issue["fields"].get("resolutiondate"))
            due = self._parse_datetime(issue["fields"].get("duedate"))
            issue_dict = {
                "jira_id": jira_id,
                "summary": summary,
                "description": convert(description),
                "assignee": assignee,
                "reporter": reporter,
                "labels": labels,
                "created": created,
                "updated": updated,
                "resolved": resolved,
                "due": due,
                "status": status,
                "project": project,
                "url": issue_url,
            }
            issue_list.append(issue_dict)

        return issue_list
