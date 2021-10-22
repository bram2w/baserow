from typing import Dict, List, Optional, Tuple

from django.db import connection

from baserow.contrib.database import models
from baserow.contrib.database.fields.models import FormulaField, Field
from baserow.contrib.database.fields.registries import (
    field_type_registry,
    field_converter_registry,
)
from baserow.contrib.database.formula.parser.update_field_names import (
    update_field_names,
)
from baserow.contrib.database.formula.types.formula_type import (
    BaserowFormulaType,
)
from baserow.contrib.database.formula.types.formula_types import (
    construct_type_from_formula_field,
)
from baserow.contrib.database.formula.types.table_typer import (
    TypedFieldWithReferences,
    TypedBaserowTable,
    type_all_fields_in_table,
)
from baserow.contrib.database.views.handler import ViewHandler


def _check_if_formula_type_change_requires_drop_recreate(
    old_formula_field: FormulaField, new_type: BaserowFormulaType
):
    old_type = construct_type_from_formula_field(old_formula_field)
    return new_type.should_recreate_when_old_type_was(old_type)


def _recreate_field_if_required(
    table: "models.Table",
    old_field: FormulaField,
    new_type: BaserowFormulaType,
    new_formula_field: FormulaField,
):
    if _check_if_formula_type_change_requires_drop_recreate(old_field, new_type):
        model = table.get_model(fields=[new_formula_field], typed_table=False)
        field_converter_registry.get("formula").alter_field(
            old_field,
            new_formula_field,
            model,
            model,
            model._meta.get_field(old_field.db_column),
            model._meta.get_field(new_formula_field.db_column),
            None,
            connection,
        )


def _calculate_and_save_updated_fields(
    table: "models.Table",
    field_name_to_typed_field: Dict[str, TypedFieldWithReferences],
    field_which_changed=None,
) -> List[Field]:
    other_changed_fields = {}
    for typed_field in field_name_to_typed_field.values():
        new_field = typed_field.new_field
        if not isinstance(new_field, FormulaField):
            continue

        typed_formula_expression = typed_field.typed_expression
        formula_field_type = typed_formula_expression.expression_type
        # noinspection PyTypeChecker
        original_formula_field: FormulaField = typed_field.original_field

        field_id = original_formula_field.id
        checking_field_which_changed = (
            field_which_changed is not None and field_which_changed.id == field_id
        )
        if checking_field_which_changed:
            formula_field_type.raise_if_invalid()

        if not (new_field.same_as(original_formula_field)):
            new_field.save()
            ViewHandler().field_type_changed(new_field)
            if not checking_field_which_changed:
                other_changed_fields[new_field.name] = new_field
                _recreate_field_if_required(
                    table, original_formula_field, formula_field_type, new_field
                )

    if field_which_changed is not None:
        # All fields that depend on the field_which_changed need to have their
        # values recalculated as a result, even if their formula or type did not
        # change as a result.
        field_name_to_typed_field[
            field_which_changed.name
        ].add_all_missing_valid_parents(other_changed_fields, field_name_to_typed_field)

    return list(other_changed_fields.values())


class TypedBaserowTableWithUpdatedFields(TypedBaserowTable):
    """
    A wrapper class containing all the typed fields in a type and additionally
    any fields which have been updated as a result of the typing of the table (possibly
    due to an initially_updated_field).
    """

    def __init__(
        self,
        typed_fields: Dict[str, TypedFieldWithReferences],
        table: "models.Table",
        initially_updated_field: Optional[Field],
        updated_fields: List[Field],
    ):
        super().__init__(typed_fields)
        self.table = table
        self.updated_initial_field = initially_updated_field
        self.updated_fields = updated_fields
        if self.updated_initial_field is not None:
            self.all_updated_fields = [self.updated_initial_field] + self.updated_fields
        else:
            self.all_updated_fields = self.updated_fields
        self.model = self.table.get_model(
            field_ids=[],
            fields=self.all_updated_fields,
            typed_table=self,
        )

    def update_values_for_all_updated_fields(self):
        """
        Does a single large update which refreshes the values of all fields which were
        updated in the table as a result of a field change.
        :return:
        """

        all_fields_update_dict = {}
        for updated_field in self.all_updated_fields:
            field_type = field_type_registry.get_by_model(updated_field)
            expr = field_type.expression_to_update_field_after_related_field_changes(
                updated_field, self.model
            )
            if expr is not None:
                all_fields_update_dict[updated_field.db_column] = expr

        # Also update trash rows so when restored they immediately have correct formula
        # values.
        self.model.objects_and_trash.update(**all_fields_update_dict)


def type_table_and_update_fields(table: "models.Table"):
    """
    This will retype all formula fields in the table, update their definitions in the
    database and return a wrapper class which can then be used to trigger a
    recalculation of the changed fields at an appropriate time.

    :param table: The table from which the field was deleted.
    :return: A wrapper object containing all updated fields and all types for fields in
        the table. The updated fields have not yet had their values recalculated as a
        and it is up to you to call pdate_values_for_all_updated_fields when appropriate
        otherwise those fields might have stale data.
    """

    typed_fields = type_all_fields_in_table(table)
    updated_fields = _calculate_and_save_updated_fields(table, typed_fields)
    return TypedBaserowTableWithUpdatedFields(typed_fields, table, None, updated_fields)


def type_table_and_update_fields_given_changed_field(
    table: "models.Table", initial_field: Field
) -> Tuple["TypedBaserowTableWithUpdatedFields", Field]:
    """
    Given the provided field has been changed in some way this will retype all formula
    fields in the table, update their definitions in the database and return a wrapper
    class which can then be used to trigger a recalculation of the changed fields at
    an appropriate time.

    :param table: The table from which the field was deleted.
    :param initial_field: The field which was changed initially.
    :return: A wrapper object containing all updated fields and all types for fields in
        the table. The updated fields have not yet had their values recalculated as a
        result of the intial_field field change and it is up to you to call
        update_values_for_all_updated_fields when appropriate otherwise those fields
        will have stale data.
    """

    typed_fields = type_all_fields_in_table(table)
    updated_fields = _calculate_and_save_updated_fields(
        table, typed_fields, field_which_changed=initial_field
    )

    if isinstance(initial_field, FormulaField):
        typed_changed_field = typed_fields[initial_field.name].new_field
    else:
        typed_changed_field = initial_field

    return (
        TypedBaserowTableWithUpdatedFields(
            typed_fields, table, typed_changed_field, updated_fields
        ),
        typed_changed_field,
    )


def update_other_fields_referencing_this_fields_name(
    field: "models.Field", new_field_name: str
):
    old_field_name = field.name
    field_updates = []
    if old_field_name != new_field_name:
        for other_field in field.table.field_set.exclude(id=field.id).all():
            other_field = other_field.specific
            if isinstance(other_field, FormulaField):
                old_formula = other_field.formula
                other_field.formula = update_field_names(
                    old_formula, {old_field_name: new_field_name}
                )
                if old_formula != other_field.formula:
                    field_updates.append(other_field)
        FormulaField.objects.bulk_update(field_updates, fields=["formula"])
    return field_updates
