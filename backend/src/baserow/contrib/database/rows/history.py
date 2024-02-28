from datetime import datetime
from typing import Any, Dict, List, NamedTuple, NewType, Optional

from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser
from django.db.models import QuerySet
from django.dispatch import receiver

from opentelemetry import trace

from baserow.contrib.database.fields.registries import field_type_registry
from baserow.contrib.database.rows.actions import UpdateRowsActionType
from baserow.contrib.database.rows.models import RowHistory
from baserow.contrib.database.rows.registries import change_row_history_registry
from baserow.contrib.database.rows.signals import rows_history_updated
from baserow.core.action.signals import ActionCommandType, action_done
from baserow.core.models import Workspace
from baserow.core.telemetry.utils import baserow_trace

tracer = trace.get_tracer(__name__)

FieldName = NewType("FieldName", str)


class RowChangeDiff(NamedTuple):
    """
    Represents the diff between the before and after values of a row. It
    contains the names of the fields that have changed, as well as the before
    and after values of those fields.
    """

    changed_field_names: List[FieldName]
    before_values: Dict[FieldName, Any]
    after_values: Dict[FieldName, Any]


class RowHistoryHandler:
    @classmethod
    def _construct_entry_from_action_and_diff(
        cls,
        user,
        table_id,
        row_id,
        field_names,
        row_fields_metadata,
        action_type,
        action_uuid,
        action_timestamp,
        action_command_type,
        diff,
    ):
        return RowHistory(
            user_id=user.id,
            user_name=user.first_name,
            table_id=table_id,
            row_id=row_id,
            field_names=field_names,
            fields_metadata=row_fields_metadata,
            action_uuid=action_uuid,
            action_command_type=action_command_type.value,
            action_timestamp=action_timestamp,
            action_type=action_type,
            before_values=diff.before_values,
            after_values=diff.after_values,
        )

    @classmethod
    def _extract_row_diff(
        cls,
        before_values: Dict[str, Any],
        after_values: Dict[str, Any],
        fields_metadata,
    ) -> Optional[RowChangeDiff]:
        """
        Extracts the fields that have changed between the before and after values of a
        row. Returns None if no fields have changed.
        """

        def are_equal(field_identifier, before_value, after_value) -> bool:
            field_type = fields_metadata[field_identifier]["type"]
            field_type = field_type_registry.get(field_type)
            return field_type.are_row_values_equal(before_value, after_value)

        changed_fields = {
            k
            for k, v in after_values.items()
            if k != "id"
            and k in before_values
            and not are_equal(k, v, before_values[k])
        }
        if not changed_fields:
            return None

        before_fields = {
            k: field_type_registry.get(
                fields_metadata[k]["type"]
            ).prepare_row_history_value_from_action_meta_data(v)
            for k, v in before_values.items()
            if k in changed_fields
        }
        after_fields = {
            k: field_type_registry.get(
                fields_metadata[k]["type"]
            ).prepare_row_history_value_from_action_meta_data(v)
            for k, v in after_values.items()
            if k in changed_fields
        }
        return RowChangeDiff(list(changed_fields), before_fields, after_fields)

    @classmethod
    def _raise_if_ids_mismatch(cls, before_values, after_values, fields_metadata):
        if (
            before_values["id"] != after_values["id"]
            or before_values["id"] != fields_metadata["id"]
        ):
            raise ValueError(
                f"Row ID mismatch between before values, after values and metadata. It should be: "
                f"{before_values['id']} == {after_values['id']} == {fields_metadata['id']}. "
                "Please ensure that the order of the rows in before, after and fields metadata "
                "are the same. This should never happen."
            )

    @classmethod
    @baserow_trace(tracer)
    def record_history_from_update_rows_action(
        cls,
        user: AbstractBaseUser,
        action_uuid: str,
        action_params: Dict[str, Any],
        action_timestamp: datetime,
        action_command_type: ActionCommandType,
    ):
        params = UpdateRowsActionType.serialized_to_params(action_params)
        after_values = params.row_values
        before_values = [
            params.original_rows_values_by_id[r["id"]] for r in after_values
        ]

        if action_command_type == ActionCommandType.UNDO:
            before_values, after_values = after_values, before_values

        row_history_entries = []
        for i, after in enumerate(after_values):
            before = before_values[i]
            fields_metadata = params.updated_fields_metadata_by_row_id[after["id"]]
            cls._raise_if_ids_mismatch(before, after, fields_metadata)

            diff = cls._extract_row_diff(before, after, fields_metadata)
            if diff is None:
                continue

            changed_fields_metadata = {
                k: v
                for k, v in fields_metadata.items()
                if k in diff.changed_field_names
            }
            row_id = after["id"]
            entry = cls._construct_entry_from_action_and_diff(
                user,
                params.table_id,
                row_id,
                diff.changed_field_names,
                changed_fields_metadata,
                UpdateRowsActionType.type,
                action_uuid,
                action_timestamp,
                action_command_type,
                diff,
            )
            row_history_entries.append(entry)

        if row_history_entries:
            row_history_entries = RowHistory.objects.bulk_create(row_history_entries)
            rows_history_updated.send(
                RowHistoryHandler,
                table_id=params.table_id,
                row_history_entries=row_history_entries,
            )

    @classmethod
    @baserow_trace(tracer)
    def list_row_history(
        cls, workspace: Workspace, table_id: int, row_id: int
    ) -> QuerySet[RowHistory]:
        """
        Returns queryset of row history entries for the provided
        workspace, table_id and row_id.
        """

        queryset = RowHistory.objects.filter(table_id=table_id, row_id=row_id).order_by(
            "-action_timestamp", "-id"
        )

        for op_type in change_row_history_registry.get_all():
            queryset = op_type.apply_to_list_queryset(
                queryset, workspace, table_id, row_id
            )

        return queryset

    @classmethod
    def delete_entries_older_than(cls, cutoff: datetime):
        """
        Deletes all row history entries that are older than the given cutoff date.

        :param cutoff: The date and time before which all entries will be deleted.
        """

        delete_qs = RowHistory.objects.filter(action_timestamp__lt=cutoff)
        delete_qs._raw_delete(delete_qs.db)


ROW_HISTORY_ACTIONS = {
    UpdateRowsActionType.type: RowHistoryHandler.record_history_from_update_rows_action,
}


@receiver(action_done)
def on_action_done_update_row_history(
    sender,
    user,
    action_type,
    action_params,
    action_timestamp,
    action_command_type,
    workspace,
    action_uuid,
    **kwargs,
):
    if settings.BASEROW_ROW_HISTORY_RETENTION_DAYS == 0:
        return

    if action_type and action_type.type in ROW_HISTORY_ACTIONS:
        add_entry_handler = ROW_HISTORY_ACTIONS[action_type.type]
        add_entry_handler(
            user, action_uuid, action_params, action_timestamp, action_command_type
        )
