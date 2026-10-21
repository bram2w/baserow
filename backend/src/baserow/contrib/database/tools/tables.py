"""
Table tools shared by the clients that act for a user. Tables and their fields are
created in one transaction. An invalid formula is reported back, never repaired
here, so this module calls no model.
"""

import json
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from itertools import groupby
from typing import Annotated, Any

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.db.models import Q
from django.utils.translation import gettext as _

from pydantic import Field, ValidationError, model_validator

from baserow.contrib.database.fields.actions import UpdateFieldActionType
from baserow.contrib.database.fields.handler import FieldHandler
from baserow.contrib.database.fields.models import Field as BaserowField
from baserow.contrib.database.fields.registries import field_type_registry
from baserow.contrib.database.models import Database
from baserow.contrib.database.table.actions import CreateTableActionType
from baserow.contrib.database.table.handler import TableHandler
from baserow.contrib.database.table.models import Table
from baserow.contrib.database.tools.fields import (
    _FIELD_EXAMPLES,
    _TYPE_ALIASES,
    BaseModel,
    FieldItem,
    FieldItemCreate,
    SelectOption,
    create_fields_in_table,
    option_value_key,
)
from baserow.core.db import specific_iterator
from baserow.core.exceptions import PermissionException
from baserow.core.service import CoreService
from baserow.core.tools import ToolContext

# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------


class BaseTableItemCreate(BaseModel):
    """Model for an existing table (with ID)."""

    name: str = Field(..., description="The name of the table.")


class BaseTableItem(BaseTableItemCreate):
    """Base model for creating a new table (no ID)."""

    id: int = Field(..., description="The unique identifier of the table.")


class TableItemCreate(BaseTableItemCreate):
    """Model for creating a table with fields."""

    primary_field_name: str = Field(
        ...,
        description="The name of the primary field (text field).",
    )
    fields: list[FieldItemCreate] = Field(..., description="The fields of the table.")

    @model_validator(mode="wrap")
    @classmethod
    def _validate_with_field_examples(cls, data, handler):
        try:
            return handler(data)
        except ValidationError as exc:
            if not isinstance(data, dict):
                raise

            table_name = data.get("name", "unknown")
            fields_data = data.get("fields", [])
            if not isinstance(fields_data, list):
                raise

            # Collect field indices that have errors
            error_field_indices: set[int] = set()
            for error in exc.errors():
                loc = error.get("loc", ())
                if len(loc) >= 2 and loc[0] == "fields" and isinstance(loc[1], int):
                    error_field_indices.add(loc[1])

            if not error_field_indices:
                raise  # No field-level errors, re-raise as-is

            error_fields = []
            error_types: set[str] = set()
            for idx in sorted(error_field_indices):
                if idx < len(fields_data) and isinstance(fields_data[idx], dict):
                    fd = fields_data[idx]
                    fname = fd.get("name", f"fields[{idx}]")
                    ftype = str(fd.get("type", "unknown"))
                    ftype = _TYPE_ALIASES.get(ftype, ftype)
                    error_fields.append(f"'{fname}' ({ftype})")
                    if ftype in _FIELD_EXAMPLES:
                        error_types.add(ftype)

            if not error_fields:
                raise

            parts = [
                f"Table '{table_name}': invalid fields: {', '.join(error_fields)}."
            ]
            for ft in sorted(error_types):
                parts.append(f"  {ft}: {json.dumps(_FIELD_EXAMPLES[ft])}")

            raise ValueError("\n".join(parts)) from None


class TableItem(BaseTableItem):
    """Model for an existing table with fields."""

    primary_field: FieldItem = Field(..., description="The primary field of the table.")
    fields: list[FieldItem] = Field(..., description="The fields of the table.")


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------


def get_tables_schema(
    tables: list[Table],
    full_schema: bool = False,
) -> list[TableItem]:
    """
    Build serialised schema descriptions for the given tables.

    :param tables: Tables to describe.
    :param full_schema: If True include all fields, otherwise only primary
        fields and relationships.
    :returns: List of table descriptions, in the same order as the input tables.
    """

    q = Q(table__in=tables)
    if not full_schema:
        q &= Q(linkrowfield__isnull=False) | Q(primary=True)

    base_field_queryset = FieldHandler().get_base_fields_queryset()
    fields = specific_iterator(
        base_field_queryset.filter(q).order_by("table_id", "order"),
        per_content_type_queryset_hook=(
            lambda field, queryset: field_type_registry.get_by_model(
                field
            ).enhance_field_queryset(queryset, field)
        ),
    )

    table_items: list[TableItem] = []
    tables_by_id = {table.id: table for table in tables}
    for table_id, fields_in_table in groupby(fields, lambda f: f.table_id):
        table_items.append(_get_table_schema(tables_by_id, table_id, fields_in_table))

    # Preserve the input order
    input_order = {t.id: i for i, t in enumerate(tables)}
    table_items.sort(key=lambda t: input_order[t.id])
    return table_items


def _get_table_schema(
    tables_by_id: dict[int, Table],
    table_id: int,
    fields_in_table: Iterable[BaserowField],
) -> TableItem:
    """
    Build a TableItem schema description for a single table given its fields.

    :param tables_by_id: Mapping of table ID → table instance for all tables.
    :param table_id: ID of the table to describe.
    :param fields_in_table: Iterable of field instances belonging to the table.
    :returns: TableItem describing the table and its fields.
    """

    fields_in_table = list(fields_in_table)
    primary_field = next((f for f in fields_in_table if f.primary), None)
    if primary_field is None:
        raise ValueError(f"Table {table_id} has no primary field")
    primary_field_item = FieldItem.from_django_orm(primary_field)

    table = tables_by_id[table_id]

    return TableItem(
        id=table_id,
        name=table.name,
        primary_field=primary_field_item,
        fields=[
            FieldItem.from_django_orm(f)
            for f in fields_in_table
            if f.id != primary_field.id
        ],
    )


# ---------------------------------------------------------------------------
# Reconciliation with exact-name tables
# ---------------------------------------------------------------------------

_FIELD_SETTINGS = {
    "long_text": ("rich_text",),
    "number": ("decimal_places", "suffix"),
    "rating": ("max_value",),
    "date": ("include_time",),
    "formula": ("formula",),
}


@dataclass(frozen=True)
class TableCreationPlan:
    """Canonical table requests and their exact-name matches."""

    requested: list[TableItemCreate]
    to_create: list[TableItemCreate]
    to_reuse: list[Table]
    conflicting_names: list[str]


def _canonical_table_requests(
    requested: Sequence[TableItemCreate],
) -> tuple[list[TableItemCreate], list[str]]:
    canonical: list[TableItemCreate] = []
    by_name: dict[str, TableItemCreate] = {}
    conflicting_names: list[str] = []

    for table in requested:
        first_request = by_name.get(table.name)
        if first_request is None:
            canonical.append(table)
            by_name[table.name] = table
            continue
        # Pydantic __eq__ ignores which settings were stated, and stated-ness routes.
        differs = table.model_dump(exclude_unset=True) != first_request.model_dump(
            exclude_unset=True
        )
        if differs and table.name not in conflicting_names:
            conflicting_names.append(table.name)

    return canonical, conflicting_names


def plan_table_creation(
    requested: Sequence[TableItemCreate], existing: Iterable[Table]
) -> TableCreationPlan:
    """
    Match requested tables to exact-name tables.

    :param requested: The requested table definitions.
    :param existing: The tables already present in the database.
    :return: The canonical requests split into tables to create and reuse.
    """

    canonical, conflicting_names = _canonical_table_requests(requested)
    existing_by_name = {table.name: table for table in existing}
    to_create: list[TableItemCreate] = []
    to_reuse: list[Table] = []

    for table in canonical:
        existing_table = existing_by_name.get(table.name)
        if existing_table is not None:
            to_reuse.append(existing_table)
            continue

        to_create.append(table)

    return TableCreationPlan(
        requested=canonical,
        to_create=to_create,
        to_reuse=to_reuse,
        conflicting_names=conflicting_names,
    )


def _find_option(options: list[SelectOption], value: str) -> SelectOption | None:
    exact = next((option for option in options if option.value == value), None)
    if exact is not None:
        return exact
    key = option_value_key(value)
    return next((o for o in options if option_value_key(o.value) == key), None)


def _select_option_conflicts(
    requested: FieldItemCreate, actual: FieldItem
) -> dict[str, Any]:
    missing, wrong_colors = [], []
    for option in requested.options or []:
        match = _find_option(actual.options or [], option.value)
        if match is None:
            missing.append(option.model_dump())
        elif option.color is not None and match.color != option.color:
            wrong_colors.append(
                {
                    "id": match.id,
                    "value": match.value,
                    "actual_color": match.color,
                    "requested_color": option.color,
                }
            )
    conflicts: dict[str, Any] = {}
    if missing:
        conflicts["missing_options"] = missing
    if wrong_colors:
        conflicts["option_color_mismatches"] = wrong_colors
    return conflicts


def _setting_conflicts(requested: FieldItemCreate, actual: FieldItem) -> dict[str, Any]:
    conflicts = {}
    for setting in _FIELD_SETTINGS.get(requested.type, ()):
        # A defaulted setting is not intent, and resolving it rewrites stored rows.
        if setting not in requested.model_fields_set:
            continue
        requested_value = getattr(requested, setting)
        actual_value = getattr(actual, setting)
        if requested_value != actual_value:
            conflicts[setting] = {
                "actual": actual_value,
                "requested": requested_value,
            }
    return conflicts


def _relation_conflicts(
    requested: FieldItemCreate,
    actual: FieldItem,
    fields_by_id: dict[int, FieldItem],
    table_ids: dict[str, int],
) -> dict[str, Any]:
    requested_table_id = (
        table_ids.get(requested.linked_table)
        if isinstance(requested.linked_table, str)
        else requested.linked_table
    )
    if requested.type == "link_row" and requested_table_id is not None:
        if requested_table_id == actual.linked_table:
            return {}
        return {
            "linked_table": {
                "actual": actual.linked_table,
                "requested": requested_table_id,
            }
        }
    if requested.type == "link_row":
        return {
            "linked_table": {
                "requested": requested.linked_table,
                "actual_id": actual.linked_table,
            }
        }
    if requested.type != "lookup":
        return {}

    through_field = fields_by_id.get(actual.through_field or -1)
    actual_table_id = through_field.linked_table if through_field else None
    conflicts: dict[str, Any] = {}
    if requested_table_id is None or requested_table_id != actual_table_id:
        conflicts["linked_table"] = {
            "actual": actual_table_id,
            "requested": requested.linked_table,
        }
    actual_target = (
        actual.target_field
        if isinstance(requested.target_field, int)
        else actual.target_field_name
    )
    if requested.target_field != actual_target:
        conflicts["target_field"] = {
            "actual": actual_target,
            "requested": requested.target_field,
        }
    return conflicts


def _field_conflict(
    requested: FieldItemCreate,
    actual: FieldItem,
    fields_by_id: dict[int, FieldItem],
    table_ids: dict[str, int],
) -> dict[str, Any] | None:
    field = {"field_id": actual.id, "name": actual.name}
    if actual.type != requested.type:
        return {
            **field,
            "actual_type": actual.type,
            "requested_type": requested.type,
        }

    conflicts: dict[str, Any] = {}
    if requested.type in {"single_select", "multiple_select"}:
        conflicts.update(_select_option_conflicts(requested, actual))
    conflicts.update(_setting_conflicts(requested, actual))
    relation_conflicts = _relation_conflicts(requested, actual, fields_by_id, table_ids)
    if relation_conflicts:
        conflicts["relation_issues"] = relation_conflicts
    return {**field, **conflicts} if conflicts else None


def _primary_field_conflict(
    requested: TableItemCreate, actual: TableItem
) -> dict[str, Any] | None:
    conflict: dict[str, Any] = {"field_id": actual.primary_field.id}
    if actual.primary_field.name != requested.primary_field_name:
        conflict.update(
            actual_name=actual.primary_field.name,
            requested_name=requested.primary_field_name,
        )
    if actual.primary_field.type != "text":
        conflict.update(actual_type=actual.primary_field.type, requested_type="text")
    return conflict if len(conflict) > 1 else None


def table_schema_conflict(
    requested: TableItemCreate,
    actual: TableItem,
    table_ids: dict[str, int] | None = None,
) -> dict[str, Any] | None:
    """
    Describe the requested schema missing from a reused table.

    :param requested: The requested table definition.
    :param actual: The actual schema of the reused table.
    :param table_ids: Mapping of requested table names to created table IDs,
        used to resolve link and lookup targets.
    :return: The conflict description, or None when the table satisfies the
        request.
    """

    primary_conflict = _primary_field_conflict(requested, actual)

    actual_fields = {field.name: field for field in actual.fields}
    fields_by_id = {field.id: field for field in actual.fields}
    missing_fields: list[dict[str, Any]] = []
    field_conflicts: list[dict[str, Any]] = []
    for requested_field in requested.fields:
        if requested_field.name.lower() == requested.primary_field_name.lower():
            continue

        actual_field = actual_fields.get(requested_field.name)
        if actual_field is None:
            missing_fields.append(
                requested_field.model_dump(exclude_none=True, exclude_unset=True)
            )
            continue

        if field_conflict := _field_conflict(
            requested_field,
            actual_field,
            fields_by_id,
            table_ids or {},
        ):
            field_conflicts.append(field_conflict)

    if not primary_conflict and not missing_fields and not field_conflicts:
        return None

    conflict: dict[str, Any] = {"id": actual.id, "name": actual.name}
    if primary_conflict:
        conflict["primary_field_mismatch"] = primary_conflict
    if missing_fields:
        conflict["missing_fields"] = missing_fields
    if field_conflicts:
        conflict["field_mismatches"] = field_conflicts
    return conflict


def missing_field_names(conflicts: Sequence[dict[str, Any]]) -> list[str]:
    """The names of the requested fields missing from the reused tables."""

    return [
        field["name"]
        for table in conflicts
        for field in table.get("missing_fields", [])
    ]


def _table_schema_conflicts(
    requested: dict[str, TableItemCreate],
    actual: Sequence[TableItem],
    table_ids: dict[str, int],
) -> list[dict[str, Any]]:
    conflicts = []
    for table in actual:
        conflict = table_schema_conflict(requested[table.name], table, table_ids)
        if conflict is not None:
            conflicts.append(conflict)
    return conflicts


def _reused_tables_next_steps(conflicts: Sequence[dict[str, Any]]) -> str:
    missing_names = missing_field_names(conflicts)
    missing_hint = (
        f" Missing fields: {', '.join(missing_names)}." if missing_names else ""
    )
    return (
        "Exact-name tables were reused, but their actual schemas in "
        "reused_tables do not satisfy the request."
        f"{missing_hint} Reuse does not authorize modifying existing tables. "
        "Unless the user already asked for these changes, confirm with them "
        "whether to modify these tables or create separate tables with different "
        "names. To complete a table, call create_fields with its id and its "
        "missing_fields payload; use update_fields for supported field settings, "
        "with missing_options as add_options and option_color_mismatches as "
        "update_options by id. Field types and link/lookup relations cannot be "
        "changed in place."
    )


def reused_table_report(
    requested: Sequence[TableItemCreate],
    actual: Sequence[TableItem],
    table_ids: dict[str, int],
) -> dict[str, Any]:
    """
    Build follow-up guidance for incomplete reused tables.

    :param requested: The requested table definitions.
    :param actual: The actual schemas of the reused tables.
    :param table_ids: Mapping of requested table names to created table IDs.
    :return: Conflicts and next_steps keys, or an empty dict when every
        reused table satisfies the request.
    """

    requested_by_name = {table.name: table for table in requested}
    conflicts = _table_schema_conflicts(requested_by_name, actual, table_ids)
    if not conflicts:
        return {}
    return {
        "incomplete_reused_tables": conflicts,
        "next_steps": _reused_tables_next_steps(conflicts),
    }


# ---------------------------------------------------------------------------
# Creation
# ---------------------------------------------------------------------------


@dataclass
class TableCreation:
    """What ``create_tables_in_database`` did."""

    plan: TableCreationPlan
    created_tables: list[Table]
    table_ids: dict[str, int]
    notes: list[str] = field(default_factory=list)
    formula_errors: list[dict[str, Any]] = field(default_factory=list)
    permission_denied: bool = False

    def to_response(self) -> dict[str, Any]:
        """The tool result, with the schemas of the tables as they are now."""

        created_items = get_tables_schema(self.created_tables, full_schema=True)
        reused_items = get_tables_schema(self.plan.to_reuse, full_schema=True)
        response: dict[str, Any] = {
            "created_tables": [table.model_dump() for table in created_items],
            "reused_tables": [table.model_dump() for table in reused_items],
            "notes": self.notes,
        }
        if self.formula_errors:
            response["formula_errors"] = self.formula_errors
        response.update(
            reused_table_report(self.plan.requested, reused_items, self.table_ids)
        )
        return response


def get_database(ctx: ToolContext, database_id: int) -> Database:
    """
    Get a database of the context's workspace.

    :raises ApplicationDoesNotExist: When the database is not in the workspace.
    """

    return CoreService().get_application(
        ctx.user,
        database_id,
        specific=False,
        base_queryset=Database.objects.filter(workspace=ctx.workspace),
    )


def _non_primary_fields(table: TableItemCreate) -> list[FieldItemCreate]:
    """Exclude the field specification represented by the primary field."""

    primary_name = table.primary_field_name.lower()
    return [field for field in table.fields if field.name.lower() != primary_name]


def _create_empty_table(
    ctx: ToolContext, database: Database, table: TableItemCreate
) -> Table:
    """Create a bare table and rename its auto-created primary field."""

    ctx.update_status(
        _("Creating table %(table_name)s...") % {"table_name": table.name}
    )
    created_table, _initial_rows = CreateTableActionType.do(
        ctx.user, database, table.name, fill_example=False
    )
    primary_field = created_table.get_primary_field().specific
    UpdateFieldActionType.do(ctx.user, primary_field, name=table.primary_field_name)
    return created_table


def _add_table_fields(
    ctx: ToolContext,
    tables: list[TableItemCreate],
    created_tables: list[Table],
    creation: TableCreation,
) -> None:
    """Create the requested fields, stopping at the first permission error."""

    for table, created_table in zip(tables, created_tables):
        try:
            # A savepoint, so a denied field keeps the tables created so far.
            with transaction.atomic():
                _, field_errors, formula_errors = create_fields_in_table(
                    ctx, created_table, _non_primary_fields(table)
                )
        except PermissionException:
            creation.notes.append(
                f"Permission denied while creating fields in "
                f"table_{created_table.id}. The tables were created, but further "
                "field setup stopped. Do not retry the denied operation."
            )
            creation.permission_denied = True
            return
        creation.notes.extend(field_errors)
        creation.formula_errors.extend(formula_errors)


def create_tables_in_database(
    ctx: ToolContext, database: Database, tables: list[TableItemCreate]
) -> TableCreation:
    """
    Create the requested tables that don't exist yet, with their fields, in one
    transaction. A table with the same name as an existing one is reused as is.

    :param ctx: Who acts and where status goes.
    :param database: The database to create the tables in.
    :param tables: The requested tables.
    :returns: The created tables, the reused ones, notes and invalid formulas.
    :raises ValidationError: When two requests use one name with different
        definitions. Nothing is created then.
    """

    # Only tables the user can see may be reused.
    existing_tables = list(
        TableHandler()
        .list_workspace_tables(ctx.user, ctx.workspace)
        .filter(database=database)
    )
    plan = plan_table_creation(tables, existing_tables)
    if plan.conflicting_names:
        names = ", ".join(plan.conflicting_names)
        raise DjangoValidationError(
            f"Conflicting table definitions use the same name: {names}. "
            "Submit one definition per table name."
        )

    with transaction.atomic():
        created_tables = [
            _create_empty_table(ctx, database, table) for table in plan.to_create
        ]
        creation = TableCreation(
            plan=plan,
            created_tables=created_tables,
            table_ids={t.name: t.id for t in [*existing_tables, *created_tables]},
        )
        _add_table_fields(ctx, plan.to_create, created_tables, creation)
    return creation


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


def create_tables(
    ctx: ToolContext,
    database_id: Annotated[
        int, Field(description="The ID of the database to create the tables in.")
    ],
    tables: Annotated[
        list[TableItemCreate],
        Field(
            min_length=1,
            description="The tables to create, each with a name, a primary field "
            "and its other fields.",
        ),
    ],
) -> dict[str, Any]:
    """
    Create tables with their fields in a database. Pass related tables in one
    call: a link_row or lookup field can name another table of the same call, and
    the reverse link field is created automatically. The primary field is always
    a text field. A table with the same name as an existing one is reused as is
    and returned with its actual schema, plus the differences when it lacks what
    was requested. A formula is stored as written. An invalid formula is not
    created: it is returned in formula_errors with the parser's message, to
    correct and add with create_fields.
    """

    database = get_database(ctx, database_id)
    return create_tables_in_database(ctx, database, tables).to_response()
