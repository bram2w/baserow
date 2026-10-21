from typing import Any, Callable

from django.contrib.auth.models import AbstractUser
from django.db import transaction

from baserow.contrib.database.fields.actions import CreateFieldActionType
from baserow.contrib.database.fields.registries import field_type_registry
from baserow.contrib.database.mcp.services import filter_tables
from baserow.contrib.database.table.models import Table
from baserow.contrib.database.tools import fields as shared_fields
from baserow.contrib.database.tools.tables import get_tables_schema  # noqa: F401
from baserow.contrib.database.views.actions import CreateViewFilterActionType
from baserow.contrib.database.views.handler import ViewHandler
from baserow.contrib.database.views.models import View, ViewFilter
from baserow.core.models import Workspace
from baserow.core.tools import ToolContext
from baserow_enterprise.assistant.tools.shared import (
    ToolInputError,
    raise_if_permission_denied,
)

from .types import (
    AnyViewFilterItemCreate,
    FieldItem,
    FieldItemUpdate,
    InvalidFormulaFieldError,
)


def get_table(user: AbstractUser, workspace: Workspace, table_id: int) -> Table:
    """
    Get a single table by ID.

    :param user: The acting user.
    :param workspace: The workspace the table must belong to.
    :param table_id: The ID of the table to fetch.
    :returns: The matching table.
    :raises ToolInputError: When the table is not visible in the workspace.
    """

    try:
        return filter_tables(user, workspace).get(id=table_id)
    except Table.DoesNotExist:
        raise ToolInputError(
            f"Table with ID {table_id} not found. "
            "Use get_tables_schema to find valid table IDs."
        )


FormulaFixer = Callable[[Table, str, str], str | None]


def create_repaired_formula_fields(
    user: AbstractUser,
    table: Table,
    formula_fixer: FormulaFixer,
    formula_errors: list[dict],
) -> tuple[list[FieldItem], list[dict]]:
    """
    Ask the formula fixer to repair each invalid formula the shared create step
    returned, and create the formula fields it repairs. Call it outside a
    transaction, because the fixer calls a model.

    :param user: The acting user.
    :param table: The table the fields belong to.
    :param formula_fixer: Callback ``(table, name, formula) -> fixed formula``.
    :param formula_errors: The invalid formulas from the shared create step.
    :returns: The created fields, and the formula errors that remain.
    """

    created: list[FieldItem] = []
    remaining: list[dict] = []
    for error in formula_errors:
        try:
            formula = formula_fixer(table, error["field_name"], error["formula"])
            if formula:
                with transaction.atomic():
                    new_field = CreateFieldActionType.do(
                        user,
                        table,
                        "formula",
                        name=error["field_name"],
                        formula=formula,
                    )
                created.append(FieldItem.from_django_orm(new_field))
                continue
        except Exception as exc:
            raise_if_permission_denied(exc)
        remaining.append(error)
    return created, remaining


def apply_repaired_formula_updates(
    tool_context: ToolContext,
    formula_fixer: FormulaFixer,
    field_updates: list[FieldItemUpdate],
    formula_errors: list[dict],
) -> tuple[list[FieldItem], bool, list[str]]:
    """
    Ask the formula fixer to repair each invalid formula the shared update step
    returned, and apply those updates with the repaired formula. Call it outside a
    transaction, because the fixer calls a model.

    :param tool_context: Who acts and where status goes.
    :param formula_fixer: Callback ``(table, name, formula) -> fixed formula``.
    :param field_updates: The updates the shared step received.
    :param formula_errors: The invalid formulas from the shared update step.
    :returns: The updated fields, whether any changed, and an error message for
        each update that could not be repaired.
    """

    updates_by_id = {update.field_id: update for update in field_updates}
    updated: list[FieldItem] = []
    changed = False
    errors: list[str] = []
    for error in formula_errors:
        field_id = error["field_id"]
        try:
            table = filter_tables(tool_context.user, tool_context.workspace).get(
                id=error["table_id"]
            )
            formula = formula_fixer(table, error["field_name"], error["formula"])
            if not formula:
                raise InvalidFormulaFieldError(
                    error["field_name"], error["formula"], table, error["error"]
                )
            update = updates_by_id[field_id].model_copy(update={"formula": formula})
            with transaction.atomic():
                field_item, field_changed = shared_fields.update_field(
                    tool_context, update
                )
            updated.append(field_item)
            changed = changed or field_changed
        except Exception as exc:
            raise_if_permission_denied(exc)
            errors.append(f"Error updating field {field_id}: {exc}")
    return updated, changed, errors


def get_view(user: AbstractUser, workspace: Workspace, view_id: int) -> View:
    """
    Fetch a view scoped to the user's workspace.

    :param user: The acting user.
    :param workspace: Workspace the view must belong to.
    :param view_id: ID of the view to retrieve.
    """

    return ViewHandler().get_view_as_user(
        user,
        view_id,
        base_queryset=View.objects.filter(table__database__workspace=workspace),
    )


def create_view_filter(
    user: AbstractUser,
    orm_view: View,
    table_fields: dict[int, Any],
    view_filter_item: AnyViewFilterItemCreate,
) -> ViewFilter:
    """
    Create a single view filter after validating the field type matches.

    :param user: The acting user.
    :param orm_view: The view to add the filter to.
    :param table_fields: Mapping of field ID → field instance for the table.
    :param view_filter_item: The filter definition to create.
    :raises ValueError: If the field is not found or its type doesn't match.
    """

    field = table_fields.get(view_filter_item.field_id)
    if field is None:
        raise ValueError(
            f"Field {view_filter_item.field_id} not found for filter. "
            f"Available field IDs: {sorted(table_fields.keys())}"
        )
    field_type = field_type_registry.get_by_model(field.specific_class)
    if field_type.type != view_filter_item.type:
        raise ValueError(
            f"Field '{field.name}' (id={field.id}) is type '{field_type.type}', "
            f"but filter declared type '{view_filter_item.type}'"
        )

    filter_type = view_filter_item.get_django_orm_type(field)
    filter_value = view_filter_item.get_django_orm_value(
        field, timezone=user.profile.timezone
    )

    return CreateViewFilterActionType.do(
        user,
        orm_view,
        field,
        filter_type,
        filter_value,
        filter_group_id=None,
    )
