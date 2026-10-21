"""
Shared database service layer.

Provides workspace-scoped access to databases, tables, fields, and rows.

All functions accept ``user`` and ``workspace`` and apply permission filtering
so callers never need to worry about permissions or cross-workspace access.
"""

from contextlib import contextmanager
from typing import Any

from django.contrib.auth.models import AbstractUser
from django.db import transaction

from baserow.api.utils import apply_exception_mapping
from baserow.contrib.database.fields.handler import FieldHandler
from baserow.contrib.database.fields.registries import field_type_registry
from baserow.contrib.database.table.handler import TableHandler
from baserow.contrib.database.table.models import Table
from baserow.core.db import specific_iterator
from baserow.core.handler import CoreHandler
from baserow.core.mcp.exceptions import MCPToolInputError, flatten_error_detail
from baserow.core.models import Workspace

# ---------------------------------------------------------------------------
# Query helpers (shared with enterprise assistant)
# ---------------------------------------------------------------------------


def _user_error_mapping() -> dict[type[Exception], Any]:
    """
    Baserow exceptions that a client causes with its input, mapped to the REST API's
    error, so REST and MCP give the same message.
    """

    from baserow.contrib.database.api.fields import errors as fe
    from baserow.contrib.database.api.rows import errors as re
    from baserow.contrib.database.fields import exceptions as f
    from baserow.contrib.database.rows import exceptions as r

    return {
        f.FieldWithSameNameAlreadyExists: fe.ERROR_FIELD_WITH_SAME_NAME_ALREADY_EXISTS,
        f.ReservedBaserowFieldNameException: fe.ERROR_RESERVED_BASEROW_FIELD_NAME,
        f.InvalidBaserowFieldName: fe.ERROR_INVALID_BASEROW_FIELD_NAME,
        f.MaxFieldNameLengthExceeded: fe.ERROR_MAX_FIELD_NAME_LENGTH_EXCEEDED,
        f.MaxFieldLimitExceeded: fe.ERROR_MAX_FIELD_COUNT_EXCEEDED,
        f.CannotCreateFieldType: fe.ERROR_CANNOT_CREATE_FIELD_TYPE,
        f.CannotChangeFieldType: fe.ERROR_CANNOT_CHANGE_FIELD_TYPE,
        f.IncompatibleField: fe.ERROR_INCOMPATIBLE_FIELD_TYPE,
        f.IncompatiblePrimaryFieldTypeError: fe.ERROR_INCOMPATIBLE_PRIMARY_FIELD_TYPE,
        f.LinkRowTableNotProvided: fe.ERROR_LINK_ROW_TABLE_NOT_PROVIDED,
        f.LinkRowTableNotInSameDatabase: fe.ERROR_LINK_ROW_TABLE_NOT_IN_SAME_DATABASE,
        f.SelfReferencingLinkRowCannotHaveRelatedField: (
            fe.ERROR_SELF_REFERENCING_LINK_ROW_CANNOT_HAVE_RELATED_FIELD
        ),
        f.FieldNotInTable: fe.ERROR_FIELD_NOT_IN_TABLE,
        f.FieldIsAlreadyPrimary: fe.ERROR_FIELD_IS_ALREADY_PRIMARY,
        f.CannotDeletePrimaryField: fe.ERROR_CANNOT_DELETE_PRIMARY_FIELD,
        f.PrimaryFieldAlreadyExists: fe.ERROR_PRIMARY_FIELD_ALREADY_EXISTS,
        f.SelectOptionDoesNotBelongToField: (
            fe.ERROR_SELECT_OPTION_DOES_NOT_BELONG_TO_FIELD
        ),
        f.InvalidFieldConstraint: fe.ERROR_INVALID_FIELD_CONSTRAINT,
        f.InvalidDefaultValueFunction: fe.ERROR_INVALID_DEFAULT_VALUE_FUNCTION,
        f.DbIndexNotSupportedError: fe.ERROR_DB_INDEX_NOT_SUPPORTED,
        f.FieldConstraintDoesNotSupportDefaultValueError: (
            fe.ERROR_FIELD_CONSTRAINT_DOES_NOT_SUPPORT_DEFAULT_VALUE
        ),
        f.FieldDataConstraintException: fe.ERROR_FIELD_DATA_CONSTRAINT,
        r.CannotCreateRowsInTable: re.ERROR_CANNOT_CREATE_ROWS_IN_TABLE,
        r.CannotDeleteRowsInTable: re.ERROR_CANNOT_DELETE_ROWS_IN_TABLE,
        r.RowIdsNotUnique: re.ERROR_ROW_IDS_NOT_UNIQUE,
    }


def _user_error_message(exc: Exception) -> str | None:
    """The REST API's message for a client error, or None for other exceptions."""

    _, error, detail = apply_exception_mapping(_user_error_mapping(), exc)
    if error is None:
        return None
    return detail or str(exc) or error.removeprefix("ERROR_").replace("_", " ").lower()


def _formula_error_types() -> tuple[type[Exception], ...]:
    from baserow.core.formula.parser.exceptions import BaserowFormulaException

    return (BaserowFormulaException,)


@contextmanager
def input_errors():
    """
    Turns known Baserow user errors raised inside the block into
    ``MCPToolInputError`` so the client gets a readable message.
    """

    from baserow.contrib.database.rows.exceptions import (
        FieldsNotWritable,
        RowDoesNotExist,
    )

    try:
        yield
    except RowDoesNotExist as exc:
        ids = ", ".join(str(i) for i in exc.ids)
        raise MCPToolInputError(f"Rows not found in this table: {ids}.") from exc
    except _formula_error_types() as exc:
        raise MCPToolInputError(f"Invalid formula: {exc}") from exc
    except FieldsNotWritable as exc:
        names = ", ".join(field.name for field in exc.fields)
        raise MCPToolInputError(
            f"You don't have permission to change these fields: {names}."
        ) from exc
    except Exception as exc:
        message = _user_error_message(exc)
        if message is None:
            raise
        raise MCPToolInputError(message) from exc


def filter_tables(user: AbstractUser, workspace: Workspace):
    """Return all tables visible to the user in the given workspace."""
    return TableHandler().list_workspace_tables(user, workspace)


def get_table(user: AbstractUser, workspace: Workspace, table_id: int) -> Table:
    """
    Return a single table by ID, verifying workspace access.

    :raises Table.DoesNotExist: if the table is not found or not accessible.
    """
    return filter_tables(user, workspace).get(id=table_id)


# ---------------------------------------------------------------------------
# Database operations
# ---------------------------------------------------------------------------


def list_databases(user: AbstractUser, workspace: Workspace) -> list:
    """
    Return all databases in the workspace that the user can see.

    :returns: List of Database instances, ordered by (order, id).
    """
    from baserow.contrib.database.models import Database
    from baserow.core.operations import ListApplicationsWorkspaceOperationType

    qs = Database.objects.filter(
        workspace=workspace,
        workspace__trashed=False,
        trashed=False,
    ).order_by("order", "id")

    return list(
        CoreHandler().filter_queryset(
            user,
            ListApplicationsWorkspaceOperationType.type,
            qs,
            workspace=workspace,
        )
    )


# ---------------------------------------------------------------------------
# Table operations
# ---------------------------------------------------------------------------


def list_tables(
    user: AbstractUser, workspace: Workspace, database_id: int | None = None
) -> list[Table]:
    """
    Return all tables visible to the user in the workspace.

    :param database_id: If provided, restrict to tables in this database.
    :returns: List of Table instances.
    """
    qs = filter_tables(user, workspace)
    if database_id is not None:
        qs = qs.filter(database_id=database_id)
    return list(qs)


def get_table_schema(
    user: AbstractUser, workspace: Workspace, table_ids: list[int]
) -> list[dict]:
    """
    Return field schemas for the given tables.

    :returns: List of dicts ``{id, name, database_id, fields: [...]}``.
              Each field dict includes ``id``, ``name``, ``type``, ``primary``
              and type-specific extras (select_options, link_row_table_id, etc.).
    """
    tables = {
        t.id: t
        for t in filter_tables(user, workspace)
        .filter(id__in=table_ids)
        .select_related("database")
    }

    valid_table_ids = [tid for tid in table_ids if tid in tables]
    if not valid_table_ids:
        return []

    all_fields = list(
        specific_iterator(
            FieldHandler()
            .get_base_fields_queryset()
            .filter(table_id__in=valid_table_ids)
            .order_by("table_id", "-primary", "order", "id"),
            per_content_type_queryset_hook=(
                lambda model, queryset: field_type_registry.get_by_model(
                    model
                ).enhance_field_queryset(queryset, model)
            ),
        )
    )

    fields_by_table: dict[int, list] = {}
    for field in all_fields:
        fields_by_table.setdefault(field.table_id, []).append(field)

    return [
        {
            "id": tables[tid].id,
            "name": tables[tid].name,
            "database_id": tables[tid].database_id,
            "fields": [_serialize_field(f) for f in fields_by_table.get(tid, [])],
        }
        for tid in valid_table_ids
    ]


def _serialize_field(field) -> dict:
    """Convert a specific field instance to a plain dict for schema output."""
    from baserow.contrib.database.fields.models import (
        DateField,
        FormulaField,
        LinkRowField,
        MultipleSelectField,
        NumberField,
        RatingField,
        SingleSelectField,
    )

    field_type = field_type_registry.get_by_model(field)
    data: dict[str, Any] = {
        "id": field.id,
        "name": field.name,
        "type": field_type.type,
        "primary": field.primary,
    }

    if isinstance(field, (SingleSelectField, MultipleSelectField)):
        data["select_options"] = [
            {"id": opt.id, "value": opt.value, "color": opt.color}
            for opt in field.select_options.all()
        ]
    elif isinstance(field, LinkRowField):
        data["link_row_table_id"] = field.link_row_table_id
        linked = field.link_row_table
        data["link_row_table_name"] = linked.name if linked else None
    elif isinstance(field, NumberField):
        data["number_decimal_places"] = field.number_decimal_places
    elif isinstance(field, DateField):
        data["date_include_time"] = field.date_include_time
        data["date_force_timezone"] = field.date_force_timezone
    elif isinstance(field, FormulaField):
        data["formula"] = field.formula
        data["formula_type"] = field.formula_type
    elif isinstance(field, RatingField):
        data["max_value"] = field.max_value

    return data


def update_table(
    user: AbstractUser, workspace: Workspace, table_id: int, name: str
) -> dict:
    """Rename a table."""
    from baserow.contrib.database.table.actions import UpdateTableActionType

    table = get_table(user, workspace, table_id)
    UpdateTableActionType.do(user, table, name=name)
    # UpdateTableActionType mutates table in-place via the handler
    return {"id": table.id, "name": table.name, "database_id": table.database_id}


def delete_table(user: AbstractUser, workspace: Workspace, table_id: int) -> None:
    """Delete (trash) a table."""
    from baserow.contrib.database.table.actions import DeleteTableActionType

    table = get_table(user, workspace, table_id)
    DeleteTableActionType.do(user, table)


# ---------------------------------------------------------------------------
# Row operations
# ---------------------------------------------------------------------------


def list_rows(
    user: AbstractUser,
    workspace: Workspace,
    table_id: int,
    search: str = "",
    page: int = 1,
    size: int = 100,
) -> dict:
    """
    Return a paginated list of rows from a table, with user field names.

    :returns: Dict with ``count`` and ``results`` (list of row dicts).
    """
    from django.conf import settings

    from baserow.contrib.database.api.rows.serializers import (
        serialize_rows_for_response,
    )

    # Clamp pagination parameters to safe bounds.
    page = max(1, page)
    size = max(1, min(size, settings.ROW_PAGE_SIZE_LIMIT))

    table = get_table(user, workspace, table_id)
    model = table.get_model()
    qs = model.objects.filter(trashed=False).order_by("order", "id")

    if search:
        qs = qs.search_all_fields(search)

    count = qs.count()
    offset = (page - 1) * size
    rows = list(qs[offset : offset + size])

    data = serialize_rows_for_response(rows, model, user_field_names=True)
    return {"count": count, "results": list(data)}


def _validate_rows(model, rows: list[dict], update: bool = False) -> list[dict]:
    """
    Validates rows keyed by user field names with the REST API's row serializer, so
    a value the API would refuse gets the same message.

    :returns: The validated rows, keyed by internal column names.
    :raises MCPToolInputError: if a value is invalid.
    """

    from baserow.api.exceptions import RequestBodyValidationException
    from baserow.api.utils import validate_data
    from baserow.contrib.database.api.rows.serializers import (
        get_batch_row_serializer_class,
        get_row_serializer_class,
    )

    _check_field_names(model, rows)
    extra = {"include_id": True, "required_fields": ["id"]} if update else {}
    row_serializer = get_row_serializer_class(model, user_field_names=True, **extra)
    try:
        data = validate_data(
            get_batch_row_serializer_class(row_serializer),
            {"items": rows},
            partial=True,
            return_validated=True,
        )
    except RequestBodyValidationException as exc:
        detail = exc.detail["detail"]
        detail = detail.get("items", detail) if isinstance(detail, dict) else detail
        problems = flatten_error_detail(detail, "rows")
        raise MCPToolInputError("Invalid value. " + "; ".join(problems)) from exc
    return data["items"]


def _check_field_names(model, rows: list[dict]):
    """
    Checks that every key of every row is ``id`` or a user field name.

    :raises MCPToolInputError: if a field name is not recognised.
    """

    names = [info["field"].name for info in model._field_objects.values()]
    for row in rows:
        for key in row:
            if key != "id" and key not in names:
                raise MCPToolInputError(
                    f"Unknown field name '{key}'. Available fields: {names}"
                )


@input_errors()
def create_rows(
    user: AbstractUser, workspace: Workspace, table_id: int, rows: list[dict]
) -> list[dict]:
    """
    Create rows in a table using user field names.

    :param rows: List of dicts mapping user field name → value.
    :returns: List of created row dicts with user field names.
    """
    from baserow.contrib.database.api.rows.serializers import (
        serialize_rows_for_response,
    )
    from baserow.contrib.database.rows.actions import CreateRowsActionType

    table = get_table(user, workspace, table_id)
    model = table.get_model()
    rows_values = _validate_rows(model, rows)
    with transaction.atomic():
        created = CreateRowsActionType.do(user, table, rows_values, model=model)
    return list(serialize_rows_for_response(created, model, user_field_names=True))


@input_errors()
def update_rows(
    user: AbstractUser, workspace: Workspace, table_id: int, rows: list[dict]
) -> list[dict]:
    """
    Update rows in a table using user field names.

    Each dict in ``rows`` must include ``id`` plus the fields to update.

    :returns: List of updated row dicts with user field names.
    """
    from baserow.contrib.database.api.rows.serializers import (
        serialize_rows_for_response,
    )
    from baserow.contrib.database.rows.actions import UpdateRowsActionType

    table = get_table(user, workspace, table_id)
    model = table.get_model()
    rows_values = _validate_rows(model, rows, update=True)
    with transaction.atomic():
        result = UpdateRowsActionType.do(user, table, rows_values, model=model)
    return list(
        serialize_rows_for_response(result.updated_rows, model, user_field_names=True)
    )


@input_errors()
def delete_rows(
    user: AbstractUser, workspace: Workspace, table_id: int, row_ids: list[int]
) -> None:
    """Delete rows by ID."""
    from baserow.contrib.database.rows.actions import DeleteRowsActionType

    table = get_table(user, workspace, table_id)
    DeleteRowsActionType.do(user, table, row_ids)
