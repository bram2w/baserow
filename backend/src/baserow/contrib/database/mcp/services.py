"""
Shared database service layer.

Provides workspace-scoped access to databases, tables, fields, and rows.

All functions accept ``user`` and ``workspace`` and apply permission filtering
so callers never need to worry about permissions or cross-workspace access.
"""

from contextlib import contextmanager

from django.contrib.auth.models import AbstractUser
from django.db import transaction

from baserow.contrib.database.table.handler import TableHandler
from baserow.contrib.database.table.models import Table
from baserow.contrib.database.tools.errors import user_error_message
from baserow.core.mcp.exceptions import MCPToolInputError, flatten_error_detail
from baserow.core.models import Workspace

# ---------------------------------------------------------------------------
# Query helpers (shared with enterprise assistant)
# ---------------------------------------------------------------------------


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
        message = user_error_message(exc)
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
# Table operations
# ---------------------------------------------------------------------------


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
